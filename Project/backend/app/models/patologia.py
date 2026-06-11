from typing import Optional, List
from datetime import date, datetime

from sqlmodel import Field, SQLModel, Relationship

from app.models.usuario import Paciente


class Patologia(SQLModel, table=True):
    __tablename__ = "patologias"
    id: Optional[int] = Field(default=None, primary_key=True)
    codigoCie11: str
    nombre: str
    categoria: str
    factorRiesgoCardiaco: bool
    pesoRiesgoModelo: float

    historiales: List["Historial"] = Relationship(back_populates="patologia")


class Historial(SQLModel, table=True):
    __tablename__ = "historiales"
    id: Optional[int] = Field(default=None, primary_key=True)
    fechaDiagnostico: date
    nivelSeveridad: str
    controlada: bool
    tratamientoActual: Optional[str] = None
    observaciones: Optional[str] = None
    ultimaRevision: datetime
    paciente_id: int = Field(foreign_key="pacientes.id")
    patologia_id: int = Field(foreign_key="patologias.id")

    paciente: Optional[Paciente] = Relationship()
    patologia: Optional[Patologia] = Relationship(back_populates="historiales")
