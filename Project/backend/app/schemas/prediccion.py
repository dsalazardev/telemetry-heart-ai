from typing import Literal
from pydantic import BaseModel


class PrediccionResponse(BaseModel):
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
    priority: Literal["BAJA", "MEDIA", "ALTA"] | None = None
    priority_score: float | None = None
    priority_level: int | None = None
    weights_version: str | None = None
