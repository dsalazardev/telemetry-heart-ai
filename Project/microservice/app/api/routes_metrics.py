import json
from logging import getLogger
from pathlib import Path

from fastapi import APIRouter, Request

from app.schemas.metrics import MetricsComparison

logger = getLogger(__name__)
router = APIRouter()


@router.get("/metrics/evaluation", response_model=MetricsComparison)
async def metrics_evaluation(request: Request):
    weights_path = request.app.state.settings.weights_path
    metrics_path = Path(weights_path)
    if metrics_path.exists():
        try:
            data = json.loads(metrics_path.read_text())
            if "metrics" in data:
                metrics_data = data["metrics"]
                return MetricsComparison(**metrics_data)
        except Exception as e:
            logger.error("Error cargando métricas: %s", e)
    return MetricsComparison(
        baseline={"recall_high_risk": 0.0, "false_negative_rate": 0.0, "f1_score": 0.0},
        optimized={"recall_high_risk": 0.0, "false_negative_rate": 0.0, "f1_score": 0.0},
        improvement={"recall_high_risk": 0.0, "false_negative_rate": 0.0, "f1_score": 0.0},
    )


@router.post("/rag/reindex")
async def rag_reindex(request: Request):
    services = request.app.state.services
    prev_state = services.rag.initialized
    services.rag.initialized = False
    try:
        services.rag.initialize()
        return {
            "status": "indexed",
            "documents": services.rag.doc_count,
            "chunks": services.rag.chunk_count,
        }
    except Exception as e:
        logger.error("Error reindexando: %s", e)
        services.rag.initialized = prev_state
        return {"status": "error", "message": str(e)}
