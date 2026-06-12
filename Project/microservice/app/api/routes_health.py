from fastapi import APIRouter, Request

from app.core.langsmith import get_client

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    services = request.app.state.services
    settings = services.settings
    client = get_client()
    return {
        "status": "ok",
        "service": "telemetry-heart-ai-microservice",
        "llm": settings.llm_provider,
        "embeddings": settings.embedding_provider,
        "chroma": "ok" if services.rag_loaded else "uninitialized",
        "postgres": "ok" if hasattr(services, "_db_ok") else "not_checked",
        "risk_engine": "weights_loaded" if services.weights_loaded else "baseline",
        "langsmith": "connected" if client is not None else "disabled",
        "agents": list(services.agents.keys()),
        "rag_loaded": services.rag_loaded,
        "weights_loaded": services.weights_loaded,
    }
