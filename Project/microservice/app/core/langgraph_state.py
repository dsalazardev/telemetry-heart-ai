from pydantic import BaseModel, ConfigDict

from app.schemas.prediction import PredictionRequest, PredictionResponse


class ClinicalState(BaseModel):
    """Estado del ClinicalGraph.

    Usa ``extra="allow"`` para preservar campos del input crudo
    de LangGraph Studio (ej. ``heart_rate``, ``spo2``) que no están
    declarados explícitamente aquí.  Sin esto, el TypedDict los descarta
    y el grafo no puede leer los datos del paciente.
    """

    model_config = ConfigDict(extra="allow")

    request: PredictionRequest | None = None
    features: dict = {}
    risk_result: dict = {}
    priority_result: object | None = None
    rag_sources: list | None = None
    clinical_explanation: str | None = None
    response: PredictionResponse | None = None
    error: str | None = None
