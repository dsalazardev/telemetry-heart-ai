import os
import sys
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock, AsyncMock

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
def setup_env():
    os.environ["ENV"] = "test"
    os.environ["environment"] = "dev"
    os.environ["embedding_provider"] = "fake"
    os.environ["llm_provider"] = "openai"
    os.environ["openai_api_key"] = "sk-test"
    os.environ["clinical_docs_path"] = str(Path(__file__).parent.parent / "app" / "data" / "clinical_docs")
    os.environ["weights_path"] = str(Path(__file__).parent.parent / "app" / "data" / "optimized_weights.json")
    yield


@pytest.fixture(scope="session")
async def setup_db():
    from app.models.lectura import Lectura
    from app.models.prediccion import Prediccion
    from app.models.adapter import Adapter

    async with test_engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Lectura.metadata.create_all(
            sync_conn, tables=[Lectura.__table__, Prediccion.__table__, Adapter.__table__]
        ))
    yield


@pytest.fixture
async def async_session():
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
async def test_client():
    from unittest.mock import patch, MagicMock
    from fastapi import APIRouter

    mock_llm = MagicMock()
    mock_llm.ainvoke = MagicMock()

    mock_rag = MagicMock()
    mock_rag.initialized = True
    mock_rag.doc_count = 1
    mock_rag.retrieve = MagicMock(return_value=[])
    mock_rag.retrieve_async = MagicMock(return_value=[])
    mock_rag.initialize = MagicMock()

    from app.services.risk_engine import RiskEngine
    mock_engine = RiskEngine(str(Path(__file__).parent.parent / "app" / "data" / "optimized_weights.json"))

    mock_settings = MagicMock()
    mock_settings.internal_token = "test-token"
    mock_settings.environment = "dev"
    mock_settings.llm_provider = "openai"
    mock_settings.embedding_provider = "fake"
    mock_settings.weights_path = str(Path(__file__).parent.parent / "app" / "data" / "optimized_weights.json")

    mock_services = MagicMock()
    mock_services.settings = mock_settings
    mock_services.rag_loaded = True
    mock_services.weights_loaded = True
    mock_services.is_ready = MagicMock(return_value=(True, []))
    mock_services.rag = mock_rag
    mock_services.llm = mock_llm
    mock_services.metrics = MagicMock()

    async def mock_n8n_run(payload: dict = None, **kwargs):
        return {"n8n_response": {"riesgo": "BAJO", "score": 0.25}}

    async def mock_clinical_run(request=None, **kwargs):
        return {
            "risk_score": 0.25,
            "risk_level": "bajo",
            "threshold_exceeded": False,
            "dominant_factors": ["test"],
            "clinical_explanation": "test explanation",
            "recommended_action": "Monitoreo continuo",
            "rag": {"used": False, "sources": []},
            "model": {"technique": "test", "weights_version": "v1", "prompt_version": "v1", "inference_time_ms": 0},
        }

    n8n_router = APIRouter()
    @n8n_router.post("/n8n/webhook")
    async def _n8n_webhook(payload: dict):
        return await mock_n8n_run(payload=payload)

    @n8n_router.post("/evaluar")
    async def _evaluar(payload: dict):
        return await mock_n8n_run(payload=payload)

    clinical_router = APIRouter()
    @clinical_router.post("/predecir")
    async def _predecir(request: dict):
        return await mock_clinical_run()

    mock_n8n_agent = MagicMock()
    mock_n8n_agent.run = mock_n8n_run
    mock_n8n_agent.router = n8n_router

    mock_clinical_agent = MagicMock()
    mock_clinical_agent.run = mock_clinical_run
    mock_clinical_agent.router = clinical_router

    mock_services.agents = {
        "clinical": mock_clinical_agent,
        "n8n": mock_n8n_agent,
        "pso": MagicMock(router=None),
    }

    with patch("app.services.Services.__init__", return_value=None), \
         patch("app.services.Services.initialize", new_callable=MagicMock):

        from app.main import app
        app.state.services = mock_services
        app.state.settings = mock_settings

        for name, agent in mock_services.agents.items():
            agent_router = getattr(agent, "router", None)
            if agent_router is not None:
                app.include_router(agent_router)

        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client
