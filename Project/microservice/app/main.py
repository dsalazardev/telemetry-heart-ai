from contextlib import asynccontextmanager
from logging import getLogger

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_health import router as health_router
from app.api.routes_metrics import router as metrics_router
from app.core.config import Settings
from app.core.logging import setup_logging
from app.services import Services

logger = getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings = Settings()
    services = Services(settings)
    await services.initialize()
    app.state.services = services
    app.state.settings = settings

    # Auto-descubrimiento de routers desde los agents
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

# Routers no asociados a agents (health, metrics se mantienen)
app.include_router(health_router, tags=["health"])
app.include_router(metrics_router, tags=["metrics"])


@app.get("/")
async def root():
    return {"service": "telemetry-heart-ai-microservice", "status": "ok"}
