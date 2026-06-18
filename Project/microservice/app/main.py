from contextlib import asynccontextmanager
from logging import getLogger
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_health import router as health_router
from app.api.routes_ready import router as ready_router
from app.api.routes_metrics import router as metrics_router
from app.api.routes_optimize import router as optimize_router
from app.api.routes_rag import router as rag_router
from app.core.config import Settings
from app.core.logging import setup_logging
from app.services import Services

logger = getLogger(__name__)


def _export_env(settings: Settings) -> None:
    if settings.openai_api_key:
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    if settings.langsmith_api_key:
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    if settings.langsmith_trace_v2:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
    if settings.langsmith_project:
        os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings = Settings()
    _export_env(settings)
    services = Services(settings)
    await services.initialize()
    app.state.services = services
    app.state.settings = settings

    for name, agent in services.agents.items():
        agent_router = getattr(agent, "router", None)
        if agent_router is not None:
            app.include_router(agent_router)
            logger.info("Router registrado: agent '%s' -> %s routes",
                        name, len(agent_router.routes))

    logger.info("Microservicio iniciado con %d agent(s)", len(services.agents))
    yield
    logger.info("Microservicio detenido")


app = FastAPI(title="Telemetry Heart AI Microservice", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, tags=["health"])
app.include_router(ready_router, tags=["health"])
app.include_router(metrics_router, tags=["metrics"])
app.include_router(optimize_router, tags=["optimize"])
app.include_router(rag_router)


@app.get("/")
async def root():
    return {"service": "telemetry-heart-ai-microservice", "status": "ok"}
