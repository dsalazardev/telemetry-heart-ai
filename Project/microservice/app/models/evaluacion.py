from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from app.models.lectura import Lectura
from app.models.prediccion import Prediccion

class Evaluacion(SQLModel, table=True):
    __tablename__ = "evaluaciones"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    fechaEvaluacion: datetime = Field(default_factory=datetime.utcnow)
    origenDatos: str = Field(..., description="telemetria | manual | batch")
    paciente_id: int = Field(..., foreign_key="pacientes.id", description="FK → pacientes.id (backend, cross-module)")
    lectura_id: int = Field(..., foreign_key="lecturas.id")
    prediccion_id: int = Field(..., foreign_key="predicciones.id")
    
    lectura: Optional[Lectura] = Relationship()
    prediccion: Optional[Prediccion] = Relationship()
