from typing import Literal

from pydantic import BaseModel, Field


class EvidenceSource(BaseModel):
    title: str
    chunk_id: str
    score: float


class ClinicalExplanation(BaseModel):
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
