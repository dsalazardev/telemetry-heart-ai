from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.clinical_subgraph import ClinicalGraph
from app.agents.pso_subgraph import PSOGraph
from app.agents.n8n_subgraph import N8NGraph


def test_clinical_graph_imports():
    assert ClinicalGraph is not None


def test_pso_graph_imports():
    assert PSOGraph is not None


def test_n8n_graph_imports():
    assert N8NGraph is not None


@pytest.mark.asyncio
async def test_clinical_graph_structure():
    from app.services.risk_engine import RiskEngine
    from app.services.rag_service import RagService

    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=MagicMock(content='{"explanation": "test"}'))

    engine = RiskEngine("nonexistent.json")
    rag = RagService(
        embedding=None,
        persist_dir="/tmp/chroma_test",
        docs_dir="/tmp/docs_test",
    )
    graph = ClinicalGraph(llm=llm, risk_engine=engine, rag=rag)
    assert graph.graph is not None
    assert hasattr(graph, "run")


@pytest.mark.asyncio
async def test_pso_graph_structure():
    from app.services.risk_engine import RiskEngine

    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=MagicMock(content="explicación mock"))

    engine = RiskEngine("nonexistent.json")
    graph = PSOGraph(llm=llm, risk_engine=engine, weights_path="/tmp/test_weights.json")
    assert graph.graph is not None
    assert hasattr(graph, "run")


@pytest.mark.asyncio
async def test_n8n_graph_structure():
    from app.services.risk_engine import RiskEngine

    engine = RiskEngine("nonexistent.json")
    graph = N8NGraph(risk_engine=engine)
    assert graph.graph is not None
    assert hasattr(graph, "run")
