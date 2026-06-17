from typing import Optional, List
from datetime import date

from sqlmodel import SQLModel, Field, Relationship


class Usuario(SQLModel, table=True):
    __tablename__ = "usuarios"
    id: Optional[int] = Field(default=None, primary_key=True)
    documento: str = Field(unique=True, index=True)
    nombres: str
    apellidos: str
    correo: str = Field(unique=True, index=True)
    password: str
    telefono: str
    activo: bool = True
    tipo: str = Field(index=True)

    paciente: Optional["Paciente"] = Relationship(back_populates="usuario")
    medico: Optional["Medico"] = Relationship(back_populates="usuario")


class Paciente(SQLModel, table=True):
    __tablename__ = "pacientes"
    id: Optional[int] = Field(default=None, foreign_key="usuarios.id", primary_key=True)
    fechaNacimiento: date

    usuario: Optional[Usuario] = Relationship(back_populates="paciente")


class Medico(SQLModel, table=True):
    __tablename__ = "medicos"
    id: Optional[int] = Field(default=None, foreign_key="usuarios.id", primary_key=True)
    especialidad: str
    licencia: str
    telegramChatId: str

    usuario: Optional[Usuario] = Relationship(back_populates="medico")
