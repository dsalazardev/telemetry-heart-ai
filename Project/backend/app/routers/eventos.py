from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.dispositivo import EventoRead, EventoCreate, EventoUpdate
from app.services import evento_service

router = APIRouter()


@router.get("", response_model=List[EventoRead])
async def listar_eventos(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models.dispositivo import Evento
    stmt = select(Evento)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=EventoRead, status_code=201)
async def crear_evento(data: EventoCreate, db: AsyncSession = Depends(get_db)):
    return await evento_service.crear_evento(db, data)


@router.post("/{evento_id}/evaluar")
async def evaluar_evento(evento_id: int, db: AsyncSession = Depends(get_db)):
    resultado = await evento_service.evaluar_umbrales(db, evento_id)
    if resultado["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return resultado
