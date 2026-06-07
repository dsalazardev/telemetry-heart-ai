from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dispositivo import Telemetria, Dispositivo
from app.schemas.dispositivo import TelemetriaCreate


def validar_telemetria(data: TelemetriaCreate) -> bool:
    if not (30 <= data.frecuenciaCardiaca <= 220):
        return False
    if not (0 <= data.spo2 <= 100):
        return False
    return True


async def crear_telemetria(db: AsyncSession, data: TelemetriaCreate) -> Telemetria:
    telemetria = Telemetria(
        frecuenciaCardiaca=data.frecuenciaCardiaca,
        anomaliaEcg=data.anomaliaEcg,
        spo2=data.spo2,
        timestamp=data.timestamp,
        dispositivo_id=data.dispositivo_id,
        estadoProcesamiento="validada",
    )
    db.add(telemetria)
    await db.commit()
    await db.refresh(telemetria)
    return telemetria


async def obtener_dispositivo(db: AsyncSession, dispositivo_id: int) -> Optional[Dispositivo]:
    stmt = select(Dispositivo).where(Dispositivo.id == dispositivo_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def enriquecer_con_lab(db: AsyncSession, telemetria_id: int, datos_lab: dict) -> Optional[Telemetria]:
    stmt = select(Telemetria).where(Telemetria.id == telemetria_id)
    result = await db.execute(stmt)
    telemetria = result.scalar_one_or_none()
    if not telemetria:
        return None
    # Agregar datos de lab como anomaliaEcg o extensión futura
    telemetria.estadoProcesamiento = "enriquecida"
    await db.commit()
    await db.refresh(telemetria)
    return telemetria
