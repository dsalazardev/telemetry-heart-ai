from typing import TypedDict, Literal

from app.schemas.prediction import PredictionRequest, PredictionResponse


class ClinicalState(TypedDict):
    request: PredictionRequest | None
    features: dict
    risk_result: dict
    rag_sources: list | None
    clinical_explanation: str | None
    response: PredictionResponse | None
    error: str | None


class PSOState(TypedDict):
    action: Literal["optimize", "explain", "compare"]
    n_particles: int
    max_iter: int
    result: dict | None
    comparison: dict | None
    explanation: str | None
    error: str | None


class N8NState(TypedDict):
    raw_payload: dict
    parsed_data: dict
    action: str
    threshold_flags: list[str]
    clinical_result: dict | None
    n8n_response: dict
    error: str | None
