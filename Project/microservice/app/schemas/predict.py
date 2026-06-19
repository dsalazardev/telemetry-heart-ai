from typing import List, Optional
from datetime import datetime
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

class EvaluarRequest(BaseModel):
    lectura: PredictRequest
    paciente_id: int
    dispositivo_id: Optional[int] = None
    workflow_id: Optional[int] = None
    origenDatos: str = "telemetria"

class EvaluarResponse(BaseModel):
    id: int
    fechaEvaluacion: datetime
    origenDatos: str
    paciente_id: int
    lectura_id: int
    prediccion_id: int
    clasificacion: str
    probabilidad: float

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    dependencies: dict
