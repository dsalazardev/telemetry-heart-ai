from typing import TypedDict

from app.schemas.prediction import PredictionRequest, PredictionResponse


class ClinicalState(TypedDict):
    request: PredictionRequest | None
    features: dict
    risk_result: dict
    priority_result: object | None
    rag_sources: list | None
    clinical_explanation: str | None
    response: PredictionResponse | None
    error: str | None
