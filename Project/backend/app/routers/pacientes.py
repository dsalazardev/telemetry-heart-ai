from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.schemas.usuario import PacienteCreate, PacienteRead, PacienteUpdate, PerfilCreate, PerfilRead, PerfilUpdate
from app.schemas.dispositivo import EventoRead
from app.services import paciente_service, evento_service

router = APIRouter()


@router.post("", response_model=PacienteRead, status_code=status.HTTP_201_CREATED)
async def crear_paciente(data: PacienteCreate, db: AsyncSession = Depends(get_db)):
    return await paciente_service.crear_paciente(db, data)


@router.get("", response_model=List[PacienteRead])
async def listar_pacientes(db: AsyncSession = Depends(get_db)):
    return await paciente_service.listar_pacientes(db)


@router.get("/{paciente_id}", response_model=PacienteRead)
async def obtener_paciente(paciente_id: int, db: AsyncSession = Depends(get_db)):
    paciente = await paciente_service.obtener_paciente(db, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return paciente


@router.put("/{paciente_id}", response_model=PacienteRead)
async def actualizar_paciente(paciente_id: int, data: PacienteUpdate, db: AsyncSession = Depends(get_db)):
    paciente = await paciente_service.actualizar_paciente(db, paciente_id, data)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return paciente


@router.delete("/{paciente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_paciente(paciente_id: int, db: AsyncSession = Depends(get_db)):
    ok = await paciente_service.eliminar_paciente(db, paciente_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return None


# ── Perfil ──
@router.post("/{paciente_id}/perfil", response_model=PerfilRead, status_code=status.HTTP_201_CREATED)
async def crear_perfil(paciente_id: int, data: PerfilCreate, db: AsyncSession = Depends(get_db)):
    return await paciente_service.crear_perfil(db, paciente_id, data)


@router.get("/{paciente_id}/perfil", response_model=PerfilRead)
async def obtener_perfil(paciente_id: int, db: AsyncSession = Depends(get_db)):
    perfil = await paciente_service.obtener_perfil(db, paciente_id)
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return perfil


@router.put("/{paciente_id}/perfil", response_model=PerfilRead)
async def actualizar_perfil(paciente_id: int, data: PerfilUpdate, db: AsyncSession = Depends(get_db)):
    perfil = await paciente_service.actualizar_perfil(db, paciente_id, data)
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return perfil


# ── Historiales ──
@router.post("/{paciente_id}/historiales", status_code=status.HTTP_201_CREATED)
async def crear_historial(paciente_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    return await paciente_service.crear_historial(db, paciente_id, data)


@router.get("/{paciente_id}/historiales")
async def listar_historiales(paciente_id: int, db: AsyncSession = Depends(get_db)):
    return await paciente_service.listar_historiales(db, paciente_id)


# ── Eventos ──
@router.get("/{paciente_id}/eventos", response_model=List[EventoRead])
async def listar_eventos_paciente(paciente_id: int, db: AsyncSession = Depends(get_db)):
    return await evento_service.listar_eventos_por_paciente(db, paciente_id)
