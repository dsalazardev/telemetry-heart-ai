from typing import Optional

from sqlmodel import Field, SQLModel, Relationship

from app.models.usuario import Paciente


class Perfil(SQLModel, table=True):
    __tablename__ = "perfiles"
    id: Optional[int] = Field(default=None, primary_key=True)
    edad: int
    sexo: str
    tipoSangre: str
    alergias: Optional[str] = None
    paciente_id: int = Field(foreign_key="pacientes.id")

    paciente: Optional[Paciente] = Relationship()
