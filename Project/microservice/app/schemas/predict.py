from typing import List, Optional
from pydantic import BaseModel


class PredictRequest(BaseModel):
    age: int
    sex: int
    cp: int
    trestbps: int
    chol: int
    fbs: bool
    restecg: int
    thalach: int
    exang: bool
    oldpeak: float
    slope: int
    ca: int
    thal: int


class PredictResponse(BaseModel):
    probabilidad: float
    clasificacion: str
    versionModelo: str
    tiempoMs: float
    importanciaVariables: Optional[dict]
    explicacionClinica: str
