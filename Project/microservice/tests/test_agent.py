from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.clinical_subgraph import ClinicalGraph


def test_clinical_graph_imports():
    assert ClinicalGraph is not None


@pytest.mark.asyncio
async def test_clinical_graph_structure():
    from app.services.risk_engine import RiskEngine
    from app.services.rag_service import RAGService
    from app.services.triage_priority_service import TriagePriorityService

    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=MagicMock(content='{"explanation": "test"}'))

    engine = RiskEngine("nonexistent.json")
    rag = RAGService(
        persist_dir="/tmp/chroma_test",
        docs_dir="/tmp/docs_test",
    )
    triage = TriagePriorityService("nonexistent.json")
    graph = ClinicalGraph(llm=llm, risk_engine=engine, rag=rag, triage_priority=triage)
    assert graph.graph is not None
    assert hasattr(graph, "run")
    assert graph.triage_priority is triage
    assert len(graph.tools) >= 1


@pytest.mark.asyncio
async def test_clinical_graph_accepts_dict_request_from_studio():
    """Reproduce el flujo de LangGraph Studio: state['request'] llega como dict.

    Antes del fix, ``req.model_dump()`` fallaba con
    ``AttributeError("'dict' object has no attribute 'model_dump'")``.
    """
    from app.services.risk_engine import RiskEngine
    from app.services.rag_service import RAGService
    from app.services.triage_priority_service import TriagePriorityService

    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=MagicMock(content='{"explanation": "test"}'))

    engine = RiskEngine("nonexistent.json")
    rag = RAGService(persist_dir="/tmp/chroma_test", docs_dir="/tmp/docs_test")
    triage = TriagePriorityService("nonexistent.json")
    graph = ClinicalGraph(llm, engine, rag, triage).graph

    initial = {
        "request": {
            "paciente_id": 1,
            "heart_rate": 160,
            "spo2": 82,
            "systolic_bp": 200,
            "diastolic_bp": 120,
            "cholesterol": 300,
            "age": 72,
            "sex": "M",
            "chest_pain_type": "asymptomatic",
            "smoker": True,
            "previous_condition": True,
            "explain": False,
        },
        "features": {},
        "risk_result": {},
        "priority_result": None,
        "rag_sources": None,
        "clinical_explanation": None,
        "response": None,
        "error": None,
    }

    result = await graph.ainvoke(initial)
    assert result.get("error") is None, f"grafo devolvió error: {result.get('error')}"
    assert result["response"] is not None
    assert result["response"].risk_score > 0.5
    assert result["response"].risk_level in ("bajo", "medio", "alto")
    assert result["response"].priority in ("BAJA", "MEDIA", "ALTA")
    assert result["response"].paciente_id == 1
    assert result["response"].weights_version == "baseline"


@pytest.mark.asyncio
async def test_chest_pain_type_influences_priority():
    """Regresión: `chest_pain_type` (string) debe mapearse al numérico que
    consume el PSO. Antes el nodo `_prioritize` leía `chest_pain` (clave
    inexistente) y la feature llegaba siempre como 0."""
    from app.services.risk_engine import RiskEngine
    from app.services.rag_service import RAGService
    from app.services.triage_priority_service import TriagePriorityService

    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=MagicMock(content='{"explanation": "x"}'))

    def _make_graph():
        engine = RiskEngine("nonexistent.json")
        rag = RAGService(persist_dir="/tmp/chroma_test", docs_dir="/tmp/docs_test")
        triage = TriagePriorityService("nonexistent.json")
        return ClinicalGraph(llm, engine, rag, triage).graph

    def _state(chest_pain_type):
        base = {
            "request": {
                "heart_rate": 120, "spo2": 92, "systolic_bp": 150,
                "diastolic_bp": 90, "cholesterol": 240, "age": 60,
                "sex": "M", "chest_pain_type": chest_pain_type,
                "smoker": True, "previous_condition": False, "explain": False,
            },
            "features": {}, "risk_result": {}, "priority_result": None,
            "rag_sources": None, "clinical_explanation": None,
            "response": None, "error": None,
        }
        return base

    low = await _make_graph().ainvoke(_state("typical_angina"))    # → 1
    high = await _make_graph().ainvoke(_state("asymptomatic"))     # → 4
    assert high["response"].priority_score > low["response"].priority_score
