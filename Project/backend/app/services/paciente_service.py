from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.usuario import Usuario, Paciente
from app.models.perfil import Perfil
from app.models.patologia import Historial
from app.schemas.usuario import PacienteCreate, PacienteUpdate, PerfilCreate, PerfilUpdate


async def crear_paciente(db: AsyncSession, data: PacienteCreate) -> Paciente:
    usuario = Usuario(
        documento=data.usuario.documento,
        nombres=data.usuario.nombres,
        apellidos=data.usuario.apellidos,
        correo=data.usuario.correo,
        password=hash_password(data.usuario.password),
        telefono=data.usuario.telefono,
        tipo="paciente",
    )
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)

    paciente = Paciente(
        id=usuario.id,
        fechaNacimiento=data.fechaNacimiento,
    )
    db.add(paciente)
    await db.commit()
    await db.refresh(paciente)
    # Eagerly load usuario for response serialization
    stmt = select(Paciente).where(Paciente.id == paciente.id).options(selectinload(Paciente.usuario))
    result = await db.execute(stmt)
    return result.scalar_one()


async def listar_pacientes(db: AsyncSession) -> List[Paciente]:
    stmt = select(Paciente).options(selectinload(Paciente.usuario))
    result = await db.execute(stmt)
    return result.scalars().all()


async def obtener_paciente(db: AsyncSession, paciente_id: int) -> Optional[Paciente]:
    stmt = select(Paciente).where(Paciente.id == paciente_id).options(selectinload(Paciente.usuario))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def actualizar_paciente(db: AsyncSession, paciente_id: int, data: PacienteUpdate) -> Optional[Paciente]:
    paciente = await obtener_paciente(db, paciente_id)
    if not paciente:
        return None
    
    # Actualizar fecha de nacimiento si viene en la data
    if data.fechaNacimiento is not None:
        paciente.fechaNacimiento = data.fechaNacimiento
    
    # Actualizar campos del usuario asociado
    if data.usuario is not None:
        if data.usuario.nombres is not None:
            paciente.usuario.nombres = data.usuario.nombres
        if data.usuario.apellidos is not None:
            paciente.usuario.apellidos = data.usuario.apellidos
        if data.usuario.correo is not None:
            paciente.usuario.correo = data.usuario.correo
        if data.usuario.telefono is not None:
            paciente.usuario.telefono = data.usuario.telefono
        if data.usuario.activo is not None:
            paciente.usuario.activo = data.usuario.activo

    await db.commit()
    await db.refresh(paciente)
    return paciente


async def eliminar_paciente(db: AsyncSession, paciente_id: int) -> bool:
    paciente = await obtener_paciente(db, paciente_id)
    if not paciente:
        return False
    await db.delete(paciente)
    await db.commit()
    return True


# ── Perfil ──
async def crear_perfil(db: AsyncSession, paciente_id: int, data: PerfilCreate) -> Perfil:
    perfil = Perfil(
        edad=data.edad,
        sexo=data.sexo,
        tipoSangre=data.tipoSangre,
        alergias=data.alergias,
        paciente_id=paciente_id,
    )
    db.add(perfil)
    await db.commit()
    await db.refresh(perfil)
    return perfil


async def obtener_perfil(db: AsyncSession, paciente_id: int) -> Optional[Perfil]:
    stmt = select(Perfil).where(Perfil.paciente_id == paciente_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def actualizar_perfil(db: AsyncSession, paciente_id: int, data: PerfilUpdate) -> Optional[Perfil]:
    perfil = await obtener_perfil(db, paciente_id)
    if not perfil:
        return None
    if data.edad is not None:
        perfil.edad = data.edad
    if data.sexo is not None:
        perfil.sexo = data.sexo
    if data.tipoSangre is not None:
        perfil.tipoSangre = data.tipoSangre
    if data.alergias is not None:
        perfil.alergias = data.alergias
    await db.commit()
    await db.refresh(perfil)
    return perfil


# ── Historial ──
async def crear_historial(db: AsyncSession, paciente_id: int, data: dict) -> Historial:
    historial = Historial(
        fechaDiagnostico=data["fechaDiagnostico"],
        nivelSeveridad=data["nivelSeveridad"],
        controlada=data["controlada"],
        tratamientoActual=data.get("tratamientoActual"),
        observaciones=data.get("observaciones"),
        ultimaRevision=data["ultimaRevision"],
        paciente_id=paciente_id,
        patologia_id=data["patologia_id"],
    )
    db.add(historial)
    await db.commit()
    await db.refresh(historial)
    return historial


async def listar_historiales(db: AsyncSession, paciente_id: int) -> List[Historial]:
    stmt = select(Historial).where(Historial.paciente_id == paciente_id)
    result = await db.execute(stmt)
    return result.scalars().all()
