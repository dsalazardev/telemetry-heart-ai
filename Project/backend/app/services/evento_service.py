from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dispositivo import Evento, Telemetria, Dispositivo
from app.schemas.dispositivo import EventoCreate
from app.services import prediccion_service


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

    resultado_pred = await prediccion_service.procesar_prediccion(
        db=db,
        datos_lectura=datos_microservicio,
        paciente_id=dispositivo.paciente_id if dispositivo else 0,
    )

    evento.valorAgregado = {
        "risk_score": resultado_pred.get("risk_score"),
        "risk_level": resultado_pred.get("risk_level"),
        "threshold_exceeded": resultado_pred.get("threshold_exceeded"),
    }
    await db.commit()
    await db.refresh(evento)

    resultado_pred["evento_id"] = evento_id
    resultado_pred["status"] = resultado_pred.get("status", "ok")
    return resultado_pred
