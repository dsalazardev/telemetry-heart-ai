from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dispositivo import Evento, Telemetria
from app.schemas.dispositivo import EventoCreate


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
    # Placeholder: en producción leería app/config/umbrales.json y compararía valorAgregado
    stmt = select(Evento).where(Evento.id == evento_id)
    result = await db.execute(stmt)
    evento = result.scalar_one_or_none()
    if not evento:
        return {"status": "not_found"}

    # Simulación: si hay más de 3 lecturas, umbral superado
    if evento.lecturas >= 3:
        return {"status": "umbral_superado", "lecturas": evento.lecturas}
    return {"status": "normal", "lecturas": evento.lecturas}
