from typing import Optional, List
from datetime import datetime

from sqlmodel import Field, SQLModel, Relationship

from app.models.usuario import Paciente, Medico

from sqlalchemy.orm import foreign, remote


class Triaje(SQLModel, table=True):
    __tablename__ = "triajes"
    id: Optional[int] = Field(default=None, primary_key=True)
    probabilidadRiesgo: float
    nivelUrgencia: str
    factoresCriticos: Optional[str] = None
    explicacionClinica: Optional[str] = None
    telegramEnviado: bool = False
    atendida: bool = False
    diagnosticoConfirmado: Optional[bool] = None
    fechaEmision: datetime = Field(default_factory=datetime.utcnow)
    fechaAtencion: Optional[datetime] = None
    workflow_id: Optional[int] = None
    paciente_id: int = Field(foreign_key="pacientes.id")
    medico_id: Optional[int] = Field(default=None, foreign_key="medicos.id")
    alerta_id: Optional[int] = Field(default=None, foreign_key="alertas.id")

    paciente: Optional[Paciente] = Relationship()
    medico: Optional[Medico] = Relationship()
    alerta: Optional["Alerta"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": lambda: Triaje.alerta_id, "overlaps": "triajes"}
    )
    logs: List["Log"] = Relationship(back_populates="triaje")


class Alerta(SQLModel, table=True):
    __tablename__ = "alertas"
    id: Optional[int] = Field(default=None, primary_key=True)
    tipo: str
    mensaje: str
    leida: bool = False
    atendida: bool = False
    fechaEmision: datetime = Field(default_factory=datetime.utcnow)
    fechaAtencion: Optional[datetime] = None
    paciente_id: int = Field(foreign_key="pacientes.id")
    medico_id: Optional[int] = Field(default=None, foreign_key="medicos.id")
    triaje_id: Optional[int] = Field(default=None, foreign_key="triajes.id")

    paciente: Optional[Paciente] = Relationship()
    medico: Optional[Medico] = Relationship()
    triaje: Optional[Triaje] = Relationship(
        sa_relationship_kwargs={"foreign_keys": lambda: Alerta.triaje_id, "overlaps": "alertas"}
    )


class Log(SQLModel, table=True):
    __tablename__ = "logs"
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tipoEvento: str
    detalle: str
    exitoso: bool
    errorMsg: Optional[str] = None
    triaje_id: int = Field(foreign_key="triajes.id")

    triaje: Optional[Triaje] = Relationship(back_populates="logs")
