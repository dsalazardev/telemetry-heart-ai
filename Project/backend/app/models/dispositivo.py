from typing import Optional, List
from datetime import datetime

from sqlalchemy import JSON
from sqlmodel import Field, SQLModel, Relationship

from app.models.usuario import Paciente


class Dispositivo(SQLModel, table=True):
    __tablename__ = "dispositivos"
    id: Optional[int] = Field(default=None, primary_key=True)
    tipo: str
    modelo: str
    sistemaOperativo: str
    tokenAutenticacion: str
    activo: bool = True
    ultimoHeartbeat: Optional[datetime] = None
    paciente_id: int = Field(foreign_key="pacientes.id")

    paciente: Optional[Paciente] = Relationship()
    telemetrias: List["Telemetria"] = Relationship()


class Telemetria(SQLModel, table=True):
    __tablename__ = "telemetrias"
    id: Optional[int] = Field(default=None, primary_key=True)
    frecuenciaCardiaca: float
    anomaliaEcg: Optional[str] = None
    spo2: float
    timestamp: datetime
    estadoProcesamiento: str = "recibida"
    dispositivo_id: int = Field(foreign_key="dispositivos.id")
    evento_id: Optional[int] = Field(default=None, foreign_key="eventos.id")

    dispositivo: Optional[Dispositivo] = Relationship()
    evento: Optional["Evento"] = Relationship()


class Evento(SQLModel, table=True):
    __tablename__ = "eventos"
    id: Optional[int] = Field(default=None, primary_key=True)
    tipo: str
    ventanaInicio: datetime
    ventanaFin: datetime
    lecturas: int = 0
    valorAgregado: Optional[dict] = Field(default=None, sa_type=JSON)
    workflow_id: Optional[int] = None

    telemetrias: List[Telemetria] = Relationship()
