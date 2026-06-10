"""Funciones puras para invocar RiskEngine y RagService.
Antes eran @tool decoradas para LangChain AgentExecutor.
Hoy se usan directamente desde los LangGraph subgraphs.
"""


def predict_risk(risk_engine, payload: dict) -> dict:
    return risk_engine.predict(payload)


def retrieve_guidelines(rag, query: str, k: int = 4) -> list[dict]:
    return rag.retrieve(query, k=k)
