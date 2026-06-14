import json
from logging import getLogger
from pathlib import Path

from fastapi import APIRouter, Request

from app.schemas.metrics import MetricsComparison, MetricsRow

logger = getLogger(__name__)
router = APIRouter()


def _empty_row() -> MetricsRow:
    return MetricsRow(
        accuracy=0.0,
        recall_high_risk=0.0,
        false_negative_rate=0.0,
        f1_score=0.0,
        critical_recall=0.0,
        overtriage_rate=0.0,
        ordinal_error=0.0,
        fitness=0.0,
    )


@router.get("/metrics/evaluation", response_model=MetricsComparison)
async def metrics_evaluation(request: Request):
    weights_path = request.app.state.settings.weights_path
    metrics_path = Path(weights_path)
    if metrics_path.exists():
        try:
            data = json.loads(metrics_path.read_text())
            if "metrics" in data:
                try:
                    return MetricsComparison(**data["metrics"])
                except Exception:
                    logger.warning("Formato de metricas invalido en %s", weights_path)
        except Exception as e:
            logger.error("Error cargando métricas: %s", e)
    return MetricsComparison(
        baseline=_empty_row(),
        optimized=_empty_row(),
        improvement=_empty_row(),
    )


@router.get("/metrics/convergence")
async def metrics_convergence(request: Request):
    weights_path = Path(request.app.state.settings.weights_path)
    curve_path = weights_path.parent / "convergence_curve.json"
    if not curve_path.exists():
        return {"convergence_curve": [], "version": "unknown", "n_iterations": 0}
    try:
        data = json.loads(curve_path.read_text())
        return {
            "convergence_curve": data.get("convergence_curve", []),
            "version": data.get("version", "unknown"),
            "n_iterations": data.get("n_iterations", 0),
        }
    except Exception as e:
        logger.error("Error cargando curva de convergencia: %s", e)
        return {"convergence_curve": [], "version": "unknown", "n_iterations": 0}
