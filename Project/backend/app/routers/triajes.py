from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.triaje import TriajeCreate, TriajeRead, TriajeUpdate, LogCreate, LogRead
from app.services import triaje_service

router = APIRouter()


@router.post("", response_model=TriajeRead, status_code=status.HTTP_201_CREATED)
async def crear_triaje(data: TriajeCreate, db: AsyncSession = Depends(get_db)):
    return await triaje_service.crear_triaje(db, data)


@router.get("", response_model=List[TriajeRead])
async def listar_triajes(db: AsyncSession = Depends(get_db)):
    return await triaje_service.listar_triajes(db)


@router.get("/pendientes", response_model=List[TriajeRead])
async def listar_pendientes(db: AsyncSession = Depends(get_db)):
    return await triaje_service.listar_triajes_pendientes(db)


@router.get("/{triaje_id}", response_model=TriajeRead)
async def obtener_triaje(triaje_id: int, db: AsyncSession = Depends(get_db)):
    triaje = await triaje_service.obtener_triaje(db, triaje_id)
    if not triaje:
        raise HTTPException(status_code=404, detail="Triaje no encontrado")
    return triaje


@router.put("/{triaje_id}/atender", response_model=TriajeRead)
async def atender_triaje(triaje_id: int, medico_id: int, db: AsyncSession = Depends(get_db)):
    triaje = await triaje_service.atender_triaje(db, triaje_id, medico_id)
    if not triaje:
        raise HTTPException(status_code=404, detail="Triaje no encontrado")
    return triaje


@router.get("/{triaje_id}/logs", response_model=List[LogRead])
async def listar_logs(triaje_id: int, db: AsyncSession = Depends(get_db)):
    return await triaje_service.listar_logs(db, triaje_id)
