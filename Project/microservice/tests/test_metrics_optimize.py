"""Tests de los endpoints /metrics/*, /optimize y la rama 503 de /ready.

Construyen una FastAPI mínima con sólo los routers bajo prueba y un
`app.state` simulado, para no depender del lifespan completo del servicio.
"""
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.routes_metrics import router as metrics_router
from app.api.routes_optimize import router as optimize_router
from app.api.routes_ready import router as ready_router

TOKEN = "test-token"


def _build_app(tmp_path: Path, *, ready=(True, [])) -> FastAPI:
    app = FastAPI()
    app.include_router(metrics_router)
    app.include_router(optimize_router)
    app.include_router(ready_router)

    settings = MagicMock()
    settings.triage_weights_path = str(tmp_path / "triage_priority_weights.json")
    settings.internal_token = TOKEN

    services = MagicMock()
    services.settings = settings
    services.is_ready = MagicMock(return_value=ready)
    services.triage_priority = MagicMock()

    app.state.settings = settings
    app.state.services = services
    return app


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ---------------------------------------------------------------- /metrics

async def test_metrics_evaluation_missing_file_returns_empty(tmp_path):
    app = _build_app(tmp_path)  # archivo no existe
    async with _client(app) as client:
        resp = await client.get("/metrics/evaluation")
    assert resp.status_code == 200
    data = resp.json()
    assert data["baseline"]["accuracy"] == 0.0
    assert data["optimized"]["accuracy"] == 0.0


async def test_metrics_evaluation_valid_file(tmp_path):
    app = _build_app(tmp_path)
    weights_path = Path(app.state.settings.triage_weights_path)
    row = {
        "accuracy": 0.9, "recall_high_risk": 0.8, "false_negative_rate": 0.1,
        "f1_score": 0.85, "critical_recall": 0.95, "overtriage_rate": 0.05,
        "ordinal_error": 0.1, "fitness": 0.3,
    }
    weights_path.write_text(json.dumps({
        "weights": [0.1] * 7,
        "metrics": {"baseline": row, "optimized": row, "improvement": row},
    }))
    async with _client(app) as client:
        resp = await client.get("/metrics/evaluation")
    assert resp.status_code == 200
    assert resp.json()["optimized"]["critical_recall"] == 0.95


async def test_metrics_convergence_missing_file(tmp_path):
    app = _build_app(tmp_path)
    async with _client(app) as client:
        resp = await client.get("/metrics/convergence")
    assert resp.status_code == 200
    data = resp.json()
    assert data["convergence_curve"] == []
    assert data["n_iterations"] == 0


async def test_metrics_convergence_valid_file(tmp_path):
    app = _build_app(tmp_path)
    curve_path = Path(app.state.settings.triage_weights_path).parent / "convergence_curve.json"
    curve_path.write_text(json.dumps({
        "convergence_curve": [0.5, 0.4, 0.3],
        "version": "pso-test",
        "n_iterations": 3,
    }))
    async with _client(app) as client:
        resp = await client.get("/metrics/convergence")
    data = resp.json()
    assert data["convergence_curve"] == [0.5, 0.4, 0.3]
    assert data["version"] == "pso-test"
    assert data["n_iterations"] == 3


# ---------------------------------------------------------------- /optimize

def _valid_payload() -> dict:
    return {
        "weights": [0.3, 0.2, 0.15, 0.1, 0.1, 0.1, 0.05],
        "thresholds": [0.30, 0.55],
        "version": "pso-test-2026",
        "algorithm": "PSO",
        "feature_weights_dict": {},
        "metrics": {"fitness": 0.25, "critical_recall": 0.9},
        "convergence_curve": [0.5, 0.3, 0.25],
    }


async def test_optimize_persists_and_reloads(tmp_path):
    app = _build_app(tmp_path)
    weights_path = Path(app.state.settings.triage_weights_path)
    async with _client(app) as client:
        resp = await client.post(
            "/optimize", json=_valid_payload(),
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "persisted"
    assert body["version"] == "pso-test-2026"
    assert body["n_iterations"] == 3
    assert body["best_fitness"] == 0.25
    # Persistió pesos y curva, y recargó el priority service
    assert weights_path.exists()
    assert (weights_path.parent / "convergence_curve.json").exists()
    app.state.services.triage_priority.reload.assert_called_once()


async def test_optimize_requires_token(tmp_path):
    app = _build_app(tmp_path)
    async with _client(app) as client:
        resp = await client.post(
            "/optimize", json=_valid_payload(),
            headers={"Authorization": "Bearer wrong"},
        )
    assert resp.status_code == 401


async def test_optimize_rejects_unordered_thresholds(tmp_path):
    app = _build_app(tmp_path)
    payload = _valid_payload()
    payload["thresholds"] = [0.8, 0.5]  # descendente
    async with _client(app) as client:
        resp = await client.post(
            "/optimize", json=payload,
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
    assert resp.status_code == 422


# ---------------------------------------------------------------- /ready 503

async def test_ready_returns_503_when_not_ready(tmp_path):
    app = _build_app(tmp_path, ready=(False, ["rag no cargado"]))
    async with _client(app) as client:
        resp = await client.get("/ready")
    assert resp.status_code == 503
    assert resp.json()["detail"]["status"] == "not_ready"
    assert "rag no cargado" in resp.json()["detail"]["errors"]
