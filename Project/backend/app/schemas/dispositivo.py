from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class DispositivoCreate(BaseModel):
    tipo: str
    modelo: str
    sistemaOperativo: str
    paciente_id: int


class DispositivoRead(BaseModel):
    id: int
    tipo: str
    modelo: str
    sistemaOperativo: str
    tokenAutenticacion: str
    activo: bool
    ultimoHeartbeat: Optional[datetime]
    paciente_id: int


class DispositivoUpdate(BaseModel):
    tipo: Optional[str] = None
    modelo: Optional[str] = None
    sistemaOperativo: Optional[str] = None
    activo: Optional[bool] = None


class TelemetriaCreate(BaseModel):
    frecuenciaCardiaca: float
    anomaliaEcg: Optional[str] = None
    spo2: float
    timestamp: datetime
    dispositivo_id: int


class TelemetriaRead(BaseModel):
    id: int
    frecuenciaCardiaca: float
    anomaliaEcg: Optional[str]
    spo2: float
    timestamp: datetime
    estadoProcesamiento: str
    dispositivo_id: int
    evento_id: Optional[int]


class EventoCreate(BaseModel):
    tipo: str
    ventanaInicio: datetime
    ventanaFin: datetime
    workflow_id: Optional[int] = None


class EventoRead(BaseModel):
    id: int
    tipo: str
    ventanaInicio: datetime
    ventanaFin: datetime
    lecturas: int
    valorAgregado: Optional[dict]
    workflow_id: Optional[int]


class EventoUpdate(BaseModel):
    lecturas: Optional[int] = None
    valorAgregado: Optional[dict] = None
    workflow_id: Optional[int] = None
