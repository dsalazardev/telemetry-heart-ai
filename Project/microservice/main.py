from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import create_tables, engine
from app.core.settings import settings
from app.routers import predict, evaluar, agent, workflow, health
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("[START] Microservice IA starting...")
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"Database URL: {settings.DATABASE_URL.split('@')[0]}@...")
    logger.info(f"Model path: {settings.MODEL_PATH}")
    logger.info(f"Chroma path: {settings.CHROMA_PATH}")
    
    # Create tables if not exists
    await create_tables()
    logger.info("[OK] Database tables created")
    
    yield
    
    # Shutdown
    logger.info("[STOP] Microservice IA shutting down...")
    await engine.dispose()

app = FastAPI(
    title="Telemetry Heart AI - Microservice",
    description="AI microservice for cardiac risk prediction, triage evaluation, and clinical assistance",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(predict.router, prefix="/predict", tags=["prediction"])
app.include_router(evaluar.router, prefix="/evaluar", tags=["evaluation"])
app.include_router(agent.router, prefix="/agent", tags=["agent"])
app.include_router(workflow.router, prefix="/workflow", tags=["workflow"])
app.include_router(health.router, prefix="/health", tags=["health"])

@app.get("/")
async def root():
    return {
        "service": "Telemetry Heart AI Microservice",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }
