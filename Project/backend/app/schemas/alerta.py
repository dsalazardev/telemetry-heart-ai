from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class AlertaCreate(BaseModel):
    tipo: str
    mensaje: str
    paciente_id: int
    medico_id: Optional[int] = None
    triaje_id: Optional[int] = None


class AlertaRead(BaseModel):
    id: int
    tipo: str
    mensaje: str
    leida: bool
    atendida: bool
    fechaEmision: datetime
    fechaAtencion: Optional[datetime]
    paciente_id: int
    medico_id: Optional[int]
    triaje_id: Optional[int]


class AlertaUpdate(BaseModel):
    leida: Optional[bool] = None
    atendida: Optional[bool] = None
    fechaAtencion: Optional[datetime] = None
    medico_id: Optional[int] = None
