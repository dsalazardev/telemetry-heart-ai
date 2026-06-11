from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

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
    from app.services.rag_service import RAGService

    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=MagicMock(content='{"explanation": "test"}'))

    engine = RiskEngine("nonexistent.json")
    rag = RAGService(
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
    llm.ainvoke = AsyncMock(return_value=MagicMock(content="explicacion mock"))

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


@pytest.mark.asyncio
async def test_agent_query(test_client: AsyncClient):
    response = await test_client.post("/agent/query", json={
        "question": "What is the risk for a 60 year old male?"
    })
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "tool_used" in data


@pytest.mark.asyncio
async def test_agent_query_empty(test_client: AsyncClient):
    response = await test_client.post("/agent/query", json={"question": ""})
    assert response.status_code == 400
