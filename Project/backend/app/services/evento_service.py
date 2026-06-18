import uuid
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dispositivo import Evento, Telemetria, Dispositivo
from app.models.usuario import Paciente
from app.schemas.dispositivo import EventoCreate
from app.services import prediccion_service


# Presets clínicos para simulación de demo. Cada uno produce un riesgo
# coherente (bajo/medio/alto) al evaluarse en el microservicio.
SIM_PRESETS = {
    "bajo": {
        "heart_rate": 72, "spo2": 98, "systolic_bp": 115, "diastolic_bp": 75,
        "cholesterol": 170, "glucose": 88, "age": 28, "sex": "F",
        "chest_pain_type": "typical_angina", "smoker": False,
        "previous_condition": False,
    },
    "medio": {
        "heart_rate": 112, "spo2": 93, "systolic_bp": 142, "diastolic_bp": 90,
        "cholesterol": 235, "glucose": 145, "age": 57, "sex": "M",
        "chest_pain_type": "atypical_angina", "smoker": True,
        "previous_condition": False,
    },
    "alto": {
        "heart_rate": 165, "spo2": 81, "systolic_bp": 200, "diastolic_bp": 122,
        "cholesterol": 305, "glucose": 250, "age": 73, "sex": "M",
        "chest_pain_type": "asymptomatic", "smoker": True,
        "previous_condition": True,
    },
}


async def simular_telemetria(
    db: AsyncSession,
    paciente_id: int,
    nivel: str = "alto",
) -> Optional[Evento]:
    """Crea un evento con una lectura de telemetría ya enlazada, para demo/pruebas.

    Asegura un dispositivo del paciente (lo crea si no existe), crea un Evento y
    una Telemetria con ``evento_id`` seteado, de modo que el evento sea visible en
    ``listar_eventos_por_paciente`` y evaluable por ``evaluar_umbrales``. El
    vector clínico completo del preset se guarda en ``evento.valorAgregado``
    (clave ``sim_features``) para que la evaluación refleje la severidad real.
    No dispara la evaluación: el usuario pulsa "Evaluar" después.

    Devuelve el Evento creado, o ``None`` si el paciente no existe.
    """
    paciente = await db.get(Paciente, paciente_id)
    if not paciente:
        return None

    preset = SIM_PRESETS.get(nivel, SIM_PRESETS["alto"])

    stmt_disp = (
        select(Dispositivo)
        .where(Dispositivo.paciente_id == paciente_id)
        .limit(1)
    )
    dispositivo = (await db.execute(stmt_disp)).scalars().first()
    if not dispositivo:
        dispositivo = Dispositivo(
            tipo="simulado",
            modelo="virtual-demo",
            sistemaOperativo="n/a",
            tokenAutenticacion=f"sim-{paciente_id}-{uuid.uuid4().hex[:8]}",
            activo=True,
            paciente_id=paciente_id,
        )
        db.add(dispositivo)
        await db.commit()
        await db.refresh(dispositivo)

    ahora = datetime.utcnow()
    evento = Evento(
        tipo="simulacion",
        ventanaInicio=ahora - timedelta(minutes=1),
        ventanaFin=ahora,
        lecturas=1,
        # Vector clínico del preset: la evaluación lo lee de aquí para
        # reflejar la severidad real del nivel simulado.
        valorAgregado={"sim_features": {**preset, "nivel": nivel}},
    )
    db.add(evento)
    await db.commit()
    await db.refresh(evento)

    telemetria = Telemetria(
        frecuenciaCardiaca=preset["heart_rate"],
        spo2=preset["spo2"],
        anomaliaEcg=f"simulacion_{nivel}",
        timestamp=ahora,
        estadoProcesamiento="recibida",
        dispositivo_id=dispositivo.id,
        evento_id=evento.id,
    )
    db.add(telemetria)
    await db.commit()
    await db.refresh(evento)

    return evento


async def listar_eventos_por_paciente(db: AsyncSession, paciente_id: int, limit: int = 50) -> List[Evento]:
    """Eventos del paciente, resueltos por el vínculo indirecto
    Evento ← Telemetria → Dispositivo → Paciente. Ordenados del más reciente al más antiguo.

    Se deduplica con un subquery ``IN`` sobre los ids de evento en vez de
    ``SELECT DISTINCT``: Postgres no puede aplicar DISTINCT cuando la fila
    incluye la columna ``valorAgregado`` (tipo ``json``, sin operador de
    igualdad)."""
    evento_ids = (
        select(Telemetria.evento_id)
        .join(Dispositivo, Dispositivo.id == Telemetria.dispositivo_id)
        .where(Dispositivo.paciente_id == paciente_id)
        .where(Telemetria.evento_id.isnot(None))
    )
    stmt = (
        select(Evento)
        .where(Evento.id.in_(evento_ids))
        .order_by(Evento.ventanaFin.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def obtener_evento_activo(db: AsyncSession, tipo: str, ventana_minutos: int = 5) -> Optional[Evento]:
    ahora = datetime.utcnow()
    inicio_ventana = ahora - timedelta(minutes=ventana_minutos)
    stmt = select(Evento).where(
        Evento.tipo == tipo,
        Evento.ventanaInicio <= ahora,
        Evento.ventanaFin >= ahora,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def crear_evento(db: AsyncSession, data: EventoCreate) -> Evento:
    evento = Evento(
        tipo=data.tipo,
        ventanaInicio=data.ventanaInicio,
        ventanaFin=data.ventanaFin,
        workflow_id=data.workflow_id,
    )
    db.add(evento)
    await db.commit()
    await db.refresh(evento)
    return evento


async def agregar_telemetria_a_evento(db: AsyncSession, telemetria: Telemetria,
                                       ventana_minutos: int = 5) -> Evento:
    evento = await obtener_evento_activo(db, "reporte_periodico", ventana_minutos)
    if not evento:
        ahora = datetime.utcnow()
        evento = Evento(
            tipo="reporte_periodico",
            ventanaInicio=ahora,
            ventanaFin=ahora + timedelta(minutes=ventana_minutos),
        )
        db.add(evento)
        await db.commit()
        await db.refresh(evento)

    telemetria.evento_id = evento.id
    evento.lecturas += 1
    await db.commit()
    await db.refresh(evento)
    return evento


async def evaluar_umbrales(db: AsyncSession, evento_id: int) -> dict:
    stmt = select(Evento).where(Evento.id == evento_id)
    result = await db.execute(stmt)
    evento = result.scalar_one_or_none()
    if not evento:
        return {"status": "not_found"}

    stmt_tel = select(Telemetria).where(Telemetria.evento_id == evento_id)
    result_tel = await db.execute(stmt_tel)
    telemetrias = result_tel.scalars().all()

    if not telemetrias:
        return {"status": "sin_telemetria", "evento_id": evento_id}

    ultima = telemetrias[-1]
    stmt_disp = select(Dispositivo).where(Dispositivo.id == ultima.dispositivo_id)
    result_disp = await db.execute(stmt_disp)
    dispositivo = result_disp.scalar_one_or_none()

    datos_microservicio = {
        "heart_rate": ultima.frecuenciaCardiaca,
        "spo2": ultima.spo2,
        "paciente_id": dispositivo.paciente_id if dispositivo else None,
        "explain": True,
    }

    # Si el evento fue simulado, usa su vector clínico completo (presión,
    # colesterol, dolor torácico, etc.) para que la predicción refleje la
    # severidad del nivel elegido y no solo FC/SpO2.
    sim_features = (evento.valorAgregado or {}).get("sim_features")
    if isinstance(sim_features, dict):
        for campo, valor in sim_features.items():
            if campo != "nivel":
                datos_microservicio.setdefault(campo, valor)

    resultado_pred = await prediccion_service.procesar_prediccion(
        db=db,
        datos_lectura=datos_microservicio,
        paciente_id=dispositivo.paciente_id if dispositivo else 0,
    )

    evento.valorAgregado = {
        # Conserva el vector simulado para re-evaluaciones posteriores.
        **({"sim_features": sim_features} if sim_features else {}),
        "risk_score": resultado_pred.get("risk_score"),
        "risk_level": resultado_pred.get("risk_level"),
        "threshold_exceeded": resultado_pred.get("threshold_exceeded"),
        "priority": resultado_pred.get("priority"),
        "priority_score": resultado_pred.get("priority_score"),
        "priority_level": resultado_pred.get("priority_level"),
    }
    await db.commit()
    await db.refresh(evento)

    resultado_pred["evento_id"] = evento_id
    resultado_pred["status"] = resultado_pred.get("status", "ok")
    return resultado_pred
