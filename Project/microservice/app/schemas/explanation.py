from typing import Literal

from pydantic import BaseModel, Field


class EvidenceSource(BaseModel):
    title: str
    chunk_id: str
    score: float


class ClinicalExplanation(BaseModel):
    """Estructura de salida del agente LangChain.
    Mapeo al modelo Triaje del backend:
      - risk_level          -> Triaje.nivelUrgencia  ("bajo"|"medio"|"alto")
      - risk_score          -> Triaje.probabilidadRiesgo
      - dominant_factors    -> Triaje.factoresCriticos (serializado como JSON string)
      - explanation         -> Triaje.explicacionClinica
      - recommended_action  -> se usa en backend para generar alerta
    """
    risk_level: Literal["bajo", "medio", "alto"]
    risk_score: float
    dominant_factors: list[str]
    explanation: str
    evidence: list[EvidenceSource]
    recommended_action: str
    limitations: str


class ExplainRequest(BaseModel):
    question: str
    prediction_context: dict | None = None


class ExplainResponse(BaseModel):
    answer: str
    sources: list[EvidenceSource]
