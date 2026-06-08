from typing import Literal

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    paciente_id: int | None = None
    evento_id: int | None = None
    heart_rate: float = Field(..., ge=0, le=300)
    spo2: float | None = Field(None, ge=0, le=100)
    systolic_bp: float | None = Field(None, ge=0, le=300)
    diastolic_bp: float | None = Field(None, ge=0, le=300)
    cholesterol: float | None = Field(None, ge=0, le=500)
    glucose: float | None = Field(None, ge=0, le=500)
    age: int | None = Field(None, ge=0, le=120)
    sex: Literal["M", "F", "O"] | None = None
    chest_pain_type: str | None = None
    smoker: bool | None = None
    previous_condition: bool | None = None
    explain: bool = True


class PredictionResponse(BaseModel):
    paciente_id: int | None = None
    evento_id: int | None = None
    risk_score: float
    risk_level: Literal["bajo", "medio", "alto"]
    threshold_exceeded: bool
    dominant_factors: list[str]
    clinical_explanation: str | None = None
    recommended_action: str
    rag: dict
    model: dict
