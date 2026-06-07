from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db
from app.models.dispositivo import Dispositivo
from app.core.security import create_device_token

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
async def crear_dispositivo(data: dict, db: AsyncSession = Depends(get_db)):
    dispositivo = Dispositivo(
        tipo=data["tipo"],
        modelo=data["modelo"],
        sistemaOperativo=data["sistemaOperativo"],
        tokenAutenticacion=create_device_token(0),  # placeholder, se actualiza luego
        paciente_id=data["paciente_id"],
    )
    db.add(dispositivo)
    await db.commit()
    await db.refresh(dispositivo)
    # Actualizar token con el ID real
    dispositivo.tokenAutenticacion = create_device_token(dispositivo.id)
    await db.commit()
    await db.refresh(dispositivo)
    return dispositivo


@router.get("", response_model=List[dict])
async def listar_dispositivos(db: AsyncSession = Depends(get_db)):
    stmt = select(Dispositivo)
    result = await db.execute(stmt)
    return result.scalars().all()
