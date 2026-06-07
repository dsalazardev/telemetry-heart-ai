from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.usuario import MedicoCreate, MedicoRead, MedicoUpdate
from app.models.usuario import Medico, Usuario
from app.core.security import hash_password
from sqlalchemy import select

router = APIRouter()


from sqlalchemy.orm import selectinload

@router.post("", response_model=MedicoRead, status_code=status.HTTP_201_CREATED)
async def crear_medico(data: MedicoCreate, db: AsyncSession = Depends(get_db)):
    usuario = Usuario(
        documento=data.usuario.documento,
        nombres=data.usuario.nombres,
        apellidos=data.usuario.apellidos,
        correo=data.usuario.correo,
        password=hash_password(data.usuario.password),
        telefono=data.usuario.telefono,
        tipo="medico",
    )
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)

    medico = Medico(
        id=usuario.id,
        especialidad=data.especialidad,
        licencia=data.licencia,
        telegramChatId=data.telegramChatId,
    )
    db.add(medico)
    await db.commit()
    await db.refresh(medico)
    # Eagerly load usuario
    stmt = select(Medico).where(Medico.id == medico.id).options(selectinload(Medico.usuario))
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get("", response_model=List[MedicoRead])
async def listar_medicos(db: AsyncSession = Depends(get_db)):
    stmt = select(Medico).options(selectinload(Medico.usuario))
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{medico_id}", response_model=MedicoRead)
async def obtener_medico(medico_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Medico).where(Medico.id == medico_id).options(selectinload(Medico.usuario))
    result = await db.execute(stmt)
    medico = result.scalar_one_or_none()
    if not medico:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    return medico


@router.put("/{medico_id}", response_model=MedicoRead)
async def actualizar_medico(medico_id: int, data: MedicoUpdate, db: AsyncSession = Depends(get_db)):
    stmt = select(Medico).where(Medico.id == medico_id)
    result = await db.execute(stmt)
    medico = result.scalar_one_or_none()
    if not medico:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    if data.especialidad is not None:
        medico.especialidad = data.especialidad
    if data.licencia is not None:
        medico.licencia = data.licencia
    if data.telegramChatId is not None:
        medico.telegramChatId = data.telegramChatId
    await db.commit()
    await db.refresh(medico)
    return medico


@router.delete("/{medico_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_medico(medico_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Medico).where(Medico.id == medico_id)
    result = await db.execute(stmt)
    medico = result.scalar_one_or_none()
    if not medico:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    await db.delete(medico)
    await db.commit()
    return None
