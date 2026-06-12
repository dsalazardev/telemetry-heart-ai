from fastapi import APIRouter, Request, HTTPException

router = APIRouter()


@router.get("/ready")
async def ready(request: Request):
    services = request.app.state.services
    ok, errors = services.is_ready()
    if not ok:
        raise HTTPException(status_code=503, detail={"status": "not_ready", "errors": errors})
    return {"status": "ready", "checks": {"embeddings": "real", "rag": "loaded", "weights": "loaded"}}
