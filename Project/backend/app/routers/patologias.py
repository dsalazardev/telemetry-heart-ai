from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db
from app.models.patologia import Patologia

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
async def crear_patologia(data: dict, db: AsyncSession = Depends(get_db)):
    patologia = Patologia(**data)
    db.add(patologia)
    await db.commit()
    await db.refresh(patologia)
    return patologia


@router.get("")
async def listar_patologias(db: AsyncSession = Depends(get_db)):
    stmt = select(Patologia)
    result = await db.execute(stmt)
    return result.scalars().all()
