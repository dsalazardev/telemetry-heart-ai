from typing import Optional, List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.triaje import Triaje, Log
from app.schemas.triaje import TriajeCreate, TriajeUpdate, LogCreate


async def crear_triaje(db: AsyncSession, data: TriajeCreate) -> Triaje:
    triaje = Triaje(
        probabilidadRiesgo=data.probabilidadRiesgo,
        nivelUrgencia=data.nivelUrgencia,
        factoresCriticos=data.factoresCriticos,
        explicacionClinica=data.explicacionClinica,
        paciente_id=data.paciente_id,
        medico_id=data.medico_id,
    )
    db.add(triaje)
    await db.commit()
    await db.refresh(triaje)
    return triaje


async def listar_triajes(db: AsyncSession) -> List[Triaje]:
    stmt = select(Triaje)
    result = await db.execute(stmt)
    return result.scalars().all()


async def listar_triajes_pendientes(db: AsyncSession) -> List[Triaje]:
    stmt = select(Triaje).where(Triaje.atendida == False)
    result = await db.execute(stmt)
    return result.scalars().all()


async def obtener_triaje(db: AsyncSession, triaje_id: int) -> Optional[Triaje]:
    stmt = select(Triaje).where(Triaje.id == triaje_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def atender_triaje(db: AsyncSession, triaje_id: int, medico_id: int) -> Optional[Triaje]:
    triaje = await obtener_triaje(db, triaje_id)
    if not triaje:
        return None
    triaje.atendida = True
    triaje.fechaAtencion = datetime.utcnow()
    triaje.medico_id = medico_id
    await db.commit()
    await db.refresh(triaje)
    return triaje


async def escalar_urgencia(db: AsyncSession, triaje_id: int, nuevo_nivel: str) -> Optional[Triaje]:
    triaje = await obtener_triaje(db, triaje_id)
    if not triaje:
        return None
    triaje.nivelUrgencia = nuevo_nivel
    await db.commit()
    await db.refresh(triaje)
    return triaje


async def notificar_telegram(db: AsyncSession, triaje_id: int) -> bool:
    # Placeholder: en producción integraría con bot de Telegram
    triaje = await obtener_triaje(db, triaje_id)
    if not triaje:
        return False
    triaje.telegramEnviado = True
    await db.commit()
    return True


async def crear_log(db: AsyncSession, data: LogCreate) -> Log:
    log = Log(
        tipoEvento=data.tipoEvento,
        detalle=data.detalle,
        exitoso=data.exitoso,
        errorMsg=data.errorMsg,
        triaje_id=data.triaje_id,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def listar_logs(db: AsyncSession, triaje_id: int) -> List[Log]:
    stmt = select(Log).where(Log.triaje_id == triaje_id)
    result = await db.execute(stmt)
    return result.scalars().all()
