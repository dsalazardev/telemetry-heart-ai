import json
from logging import getLogger
from pathlib import Path

from fastapi import APIRouter, Depends, Request

from app.core.dependencies import get_services, verify_internal_token
from app.schemas.optimize import OptimizeUploadRequest, OptimizeUploadResponse

logger = getLogger(__name__)
router = APIRouter(tags=["optimize"])


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


@router.post(
    "/optimize",
    response_model=OptimizeUploadResponse,
    dependencies=[Depends(verify_internal_token)],
)
async def upload_optimized_weights(
    req: OptimizeUploadRequest,
    request: Request,
):
    """Persiste pesos PSO + curva de convergencia y recarga el priority service.

    Este endpoint NO ejecuta PSO; sólo ingiere el resultado de una corrida
    (típicamente disparada por el `@tool optimize_triage_priority_tool` desde
    LangGraph Studio o un script offline).
    """
    services = request.app.state.services
    settings = services.settings

    weights_path = Path(settings.triage_weights_path)
    weights_payload = {
        "weights": req.weights,
        "thresholds": req.thresholds,
        "feature_weights_dict": req.feature_weights_dict,
        "version": req.version,
        "algorithm": req.algorithm,
        "metrics": req.metrics,
    }
    _write_json(weights_path, weights_payload)
    logger.info("Pesos PSO persistidos en %s (version=%s)", weights_path, req.version)

    curve_path: Path | None = None
    if req.convergence_curve:
        curve_path = weights_path.parent / "convergence_curve.json"
        curve_payload = {
            "convergence_curve": req.convergence_curve,
            "version": req.version,
            "n_iterations": len(req.convergence_curve),
        }
        _write_json(curve_path, curve_payload)
        logger.info("Curva de convergencia persistida en %s", curve_path)

    services.triage_priority.reload()

    return OptimizeUploadResponse(
        status="persisted",
        version=req.version,
        weights_path=str(weights_path),
        curve_path=str(curve_path) if curve_path else None,
        n_iterations=len(req.convergence_curve),
        best_fitness=float(req.metrics.get("fitness", 0.0)),
        critical_recall=req.metrics.get("critical_recall"),
    )
