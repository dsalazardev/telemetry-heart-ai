from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    services = request.app.state.services
    return {
        "status": "ok",
        "service": "telemetry-heart-ai-microservice",
        "rag_loaded": services.rag_loaded,
        "weights_loaded": services.weights_loaded,
    }
