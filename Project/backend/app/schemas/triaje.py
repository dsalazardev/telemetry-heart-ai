from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class TriajeCreate(BaseModel):
    probabilidadRiesgo: float
    nivelUrgencia: str
    factoresCriticos: Optional[str] = None
    explicacionClinica: Optional[str] = None
    paciente_id: int
    medico_id: Optional[int] = None


class TriajeRead(BaseModel):
    id: int
    probabilidadRiesgo: float
    nivelUrgencia: str
    factoresCriticos: Optional[str]
    explicacionClinica: Optional[str]
    telegramEnviado: bool
    atendida: bool
    diagnosticoConfirmado: Optional[bool]
    fechaEmision: datetime
    fechaAtencion: Optional[datetime]
    paciente_id: int
    medico_id: Optional[int]
    alerta_id: Optional[int]


class TriajeUpdate(BaseModel):
    probabilidadRiesgo: Optional[float] = None
    nivelUrgencia: Optional[str] = None
    factoresCriticos: Optional[str] = None
    explicacionClinica: Optional[str] = None
    atendida: Optional[bool] = None
    diagnosticoConfirmado: Optional[bool] = None
    fechaAtencion: Optional[datetime] = None
    medico_id: Optional[int] = None


class LogCreate(BaseModel):
    tipoEvento: str
    detalle: str
    exitoso: bool
    errorMsg: Optional[str] = None
    triaje_id: int


class LogRead(BaseModel):
    id: int
    timestamp: datetime
    tipoEvento: str
    detalle: str
    exitoso: bool
    errorMsg: Optional[str]
    triaje_id: int
