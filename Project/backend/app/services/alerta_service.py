from typing import Optional, List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.triaje import Alerta


async def crear_alerta(db: AsyncSession, tipo: str, mensaje: str, paciente_id: int,
                       medico_id: Optional[int] = None, triaje_id: Optional[int] = None) -> Alerta:
    alerta = Alerta(
        tipo=tipo,
        mensaje=mensaje,
        paciente_id=paciente_id,
        medico_id=medico_id,
        triaje_id=triaje_id,
    )
    db.add(alerta)
    await db.commit()
    await db.refresh(alerta)
    return alerta


async def listar_alertas(db: AsyncSession, atendida: Optional[bool] = None) -> List[Alerta]:
    stmt = select(Alerta)
    if atendida is not None:
        stmt = stmt.where(Alerta.atendida == atendida)
    result = await db.execute(stmt)
    return result.scalars().all()


async def obtener_alerta(db: AsyncSession, alerta_id: int) -> Optional[Alerta]:
    stmt = select(Alerta).where(Alerta.id == alerta_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def marcar_leida(db: AsyncSession, alerta_id: int) -> Optional[Alerta]:
    alerta = await obtener_alerta(db, alerta_id)
    if not alerta:
        return None
    alerta.leida = True
    await db.commit()
    await db.refresh(alerta)
    return alerta


async def asignar_medico(db: AsyncSession, alerta_id: int, medico_id: int) -> Optional[Alerta]:
    alerta = await obtener_alerta(db, alerta_id)
    if not alerta:
        return None
    alerta.medico_id = medico_id
    await db.commit()
    await db.refresh(alerta)
    return alerta


async def atender_alerta(db: AsyncSession, alerta_id: int) -> Optional[Alerta]:
    alerta = await obtener_alerta(db, alerta_id)
    if not alerta:
        return None
    alerta.atendida = True
    alerta.fechaAtencion = datetime.utcnow()
    await db.commit()
    await db.refresh(alerta)
    return alerta
