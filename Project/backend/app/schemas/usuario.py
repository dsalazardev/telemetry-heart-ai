from typing import Optional
from datetime import date
from pydantic import BaseModel


# ── Usuario ──
class UsuarioCreate(BaseModel):
    documento: str
    nombres: str
    apellidos: str
    correo: str
    password: str
    telefono: str


class UsuarioRead(BaseModel):
    id: int
    documento: str
    nombres: str
    apellidos: str
    correo: str
    telefono: str
    activo: bool
    tipo: str


class UsuarioUpdate(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    correo: Optional[str] = None
    telefono: Optional[str] = None
    activo: Optional[bool] = None


# ── Paciente ──
class PacienteCreate(BaseModel):
    usuario: UsuarioCreate
    fechaNacimiento: date


class PacienteRead(BaseModel):
    id: int
    fechaNacimiento: date
    usuario: UsuarioRead


class PacienteUpdate(BaseModel):
    fechaNacimiento: Optional[date] = None
    usuario: Optional[UsuarioUpdate] = None


# ── Medico ──
class MedicoCreate(BaseModel):
    usuario: UsuarioCreate
    especialidad: str
    licencia: str
    telegramChatId: str


class MedicoRead(BaseModel):
    id: int
    especialidad: str
    licencia: str
    telegramChatId: str
    usuario: UsuarioRead


class MedicoUpdate(BaseModel):
    especialidad: Optional[str] = None
    licencia: Optional[str] = None
    telegramChatId: Optional[str] = None
    usuario: Optional[UsuarioUpdate] = None


# ── Perfil ──
class PerfilCreate(BaseModel):
    edad: int
    sexo: str
    tipoSangre: str
    alergias: Optional[str] = None


class PerfilRead(BaseModel):
    id: int
    edad: int
    sexo: str
    tipoSangre: str
    alergias: Optional[str]


class PerfilUpdate(BaseModel):
    edad: Optional[int] = None
    sexo: Optional[str] = None
    tipoSangre: Optional[str] = None
    alergias: Optional[str] = None


# ── Auth ──
class LoginRequest(BaseModel):
    correo: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
