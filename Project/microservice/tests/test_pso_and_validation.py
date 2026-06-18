"""Tests de la validación cruzada de PredictionRequest y mejoras del PSO
(parada temprana + bounds de umbrales parametrizables)."""
import numpy as np
import pytest
from pydantic import ValidationError

from app.schemas.prediction import PredictionRequest
from app.services.optimizers.pso import PSOOptimizer


# ---------------------------------------------------- validación de presión

def test_systolic_must_exceed_diastolic():
    with pytest.raises(ValidationError, match="systolic_bp"):
        PredictionRequest(heart_rate=80, systolic_bp=80, diastolic_bp=120)


def test_valid_blood_pressure_accepted():
    req = PredictionRequest(heart_rate=80, systolic_bp=120, diastolic_bp=80)
    assert req.systolic_bp == 120


def test_missing_diastolic_skips_cross_validation():
    req = PredictionRequest(heart_rate=80, systolic_bp=120)
    assert req.diastolic_bp is None


# ---------------------------------------------------- PSO mejoras

def _toy_dataset():
    rng = np.random.default_rng(0)
    X = rng.uniform(0, 1, size=(40, 7))
    y = rng.integers(0, 3, size=40)
    return X, y


def test_pso_custom_threshold_bounds_respected():
    X, y = _toy_dataset()
    opt = PSOOptimizer(
        n_particles=8, max_iter=5,
        threshold_lb=(0.20, 0.40), threshold_ub=(0.35, 0.65),
    )
    result = opt.optimize(X, y)
    t_medium, t_high = result.thresholds
    assert 0.20 <= t_medium <= 0.65  # ordenados tras sort, dentro del rango global
    assert t_medium <= t_high


def test_pso_early_stopping_reduces_iterations():
    X, y = _toy_dataset()
    opt = PSOOptimizer(n_particles=6, max_iter=200, patience=3, seed=1)
    result = opt.optimize(X, y)
    # Con paciencia=3 debe converger bastante antes del tope de 200
    assert result.n_generations < 200
    assert len(result.convergence_curve) == result.n_generations


def test_pso_no_early_stopping_runs_full_iterations():
    X, y = _toy_dataset()
    opt = PSOOptimizer(n_particles=6, max_iter=10, patience=None, seed=1)
    result = opt.optimize(X, y)
    assert result.n_generations == 10
