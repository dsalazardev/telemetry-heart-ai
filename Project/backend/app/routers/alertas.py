from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.alerta import AlertaCreate, AlertaRead, AlertaUpdate
from app.services import alerta_service

router = APIRouter()


@router.get("", response_model=List[AlertaRead])
async def listar_alertas(atendida: Optional[bool] = None, db: AsyncSession = Depends(get_db)):
    return await alerta_service.listar_alertas(db, atendida=atendida)


@router.post("", response_model=AlertaRead, status_code=status.HTTP_201_CREATED)
async def crear_alerta(data: AlertaCreate, db: AsyncSession = Depends(get_db)):
    return await alerta_service.crear_alerta(
        db, data.tipo, data.mensaje, data.paciente_id, data.medico_id, data.triaje_id
    )


@router.put("/{alerta_id}/leer", response_model=AlertaRead)
async def marcar_leida(alerta_id: int, db: AsyncSession = Depends(get_db)):
    alerta = await alerta_service.marcar_leida(db, alerta_id)
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return alerta


@router.put("/{alerta_id}/asignar", response_model=AlertaRead)
async def asignar_medico(alerta_id: int, medico_id: int, db: AsyncSession = Depends(get_db)):
    alerta = await alerta_service.asignar_medico(db, alerta_id, medico_id)
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return alerta


@router.put("/{alerta_id}/atender", response_model=AlertaRead)
async def atender_alerta(alerta_id: int, db: AsyncSession = Depends(get_db)):
    alerta = await alerta_service.atender_alerta(db, alerta_id)
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return alerta
