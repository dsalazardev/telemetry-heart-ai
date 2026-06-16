from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.explanation import ClinicalExplanation


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

    @model_validator(mode="after")
    def _check_blood_pressure(self) -> "PredictionRequest":
        """Valida coherencia entre presiones: sistólica > diastólica.

        Los rangos por campo (`ge`/`le`) no detectan combinaciones
        fisiológicamente imposibles como systolic=80, diastolic=120.
        """
        if self.systolic_bp is not None and self.diastolic_bp is not None:
            if self.systolic_bp <= self.diastolic_bp:
                raise ValueError(
                    f"systolic_bp ({self.systolic_bp}) debe ser mayor que "
                    f"diastolic_bp ({self.diastolic_bp})"
                )
        return self


class PredictionResponse(BaseModel):
    paciente_id: int | None = None
    evento_id: int | None = None
    risk_score: float
    risk_level: Literal["bajo", "medio", "alto"]
    threshold_exceeded: bool
    dominant_factors: list[str]
    clinical_explanation: str | None = None
    explanation_structured: ClinicalExplanation | None = None
    recommended_action: str
    rag: dict
    model: dict

    priority: Literal["BAJA", "MEDIA", "ALTA"] | None = None
    priority_score: float | None = None
    priority_level: int | None = None
    weights_version: str | None = None
