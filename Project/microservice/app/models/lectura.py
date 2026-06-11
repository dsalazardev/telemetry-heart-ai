from __future__ import annotations

from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field

class Lectura(SQLModel, table=True):
    __tablename__ = "lecturas"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    age: int = Field(..., description="Edad en años")
    sex: int = Field(..., description="1 = masculino, 0 = femenino")
    cp: int = Field(..., description="Tipo de dolor torácico (0-3)")
    trestbps: int = Field(..., description="Presión arterial en reposo (mmHg)")
    chol: int = Field(..., description="Colesterol sérico (mg/dl)")
    fbs: bool = Field(..., description="Glucosa en ayunas > 120 mg/dl")
    restecg: int = Field(..., description="Resultados electrocardiográficos (0-2)")
    thalach: int = Field(..., description="Frecuencia cardíaca máxima alcanzada")
    exang: bool = Field(..., description="Angina inducida por ejercicio")
    oldpeak: float = Field(..., description="Depresión ST inducida por ejercicio")
    slope: int = Field(..., description="Pendiente del segmento ST (0-2)")
    ca: int = Field(..., description="Número de vasos principales coloreados (0-3)")
    thal: int = Field(..., description="Talasemia (0-3)")
    target: Optional[bool] = Field(default=None, description="null = pendiente, true = enfermo, false = sano")
    fechaCreacion: datetime = Field(default_factory=datetime.utcnow)
    
    def exportarVector(self) -> List[float]:
        """Devuelve las 13 features como vector numérico"""
        return [
            float(self.age), float(self.sex), float(self.cp),
            float(self.trestbps), float(self.chol), float(self.fbs),
            float(self.restecg), float(self.thalach), float(self.exang),
            self.oldpeak, float(self.slope), float(self.ca), float(self.thal)
        ]
