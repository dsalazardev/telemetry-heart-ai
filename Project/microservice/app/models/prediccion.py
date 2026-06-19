from typing import Optional, Dict, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import JSON
from app.models.documento import Documento

class Prediccion(SQLModel, table=True):
    __tablename__ = "predicciones"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    versionModelo: str = Field(..., description="Versión del modelo (ej: rf-v1.2)")
    probabilidad: float = Field(..., description="Probabilidad de riesgo (0.0 - 1.0)")
    clasificacion: str = Field(..., description="bajo | medio | alto")
    importanciaVariables: Optional[Dict] = Field(default=None, sa_type=JSON)
    tiempoMs: float = Field(..., description="Tiempo de inferencia en milisegundos")
    fecha: datetime = Field(default_factory=datetime.utcnow)
    metadataTecnica: Optional[Dict] = Field(default=None, sa_type=JSON)
    
    documentos: List[Documento] = Relationship()
    
    def interpretarResultado(self) -> str:
        """Devuelve: 'Riesgo {clasificacion}: {probabilidad:.1%}'"""
        return f"Riesgo {self.clasificacion}: {self.probabilidad:.1%}"
