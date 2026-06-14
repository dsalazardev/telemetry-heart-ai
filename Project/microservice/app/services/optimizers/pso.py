"""PSO optimizer for cardiovascular triage priority.

Codificación de partícula (10 dimensiones):
  - 7 pesos clínicos (∈ [0, 1]):
      0: heart_rate
      1: spo2
      2: systolic_bp
      3: cholesterol
      4: chest_pain
      5: age
      6: other (smoker/previous_condition promedio)
  - 3 umbrales ordenados (∈ [0, 1]):
      7: t_medium
      8: t_high
      9: t_critical

Función objetivo (minimizar):
  F = ordinal_error
    + 3.0 * critical_false_negative_rate
    + 0.5 * overtriage_rate

Donde:
  - ordinal_error          = mean(|pred - y_true|) / 3, ∈ [0, 1]
  - critical_FN_rate       = proporción de casos críticos subclasificados
  - overtriage_rate        = proporción de no-críticos sobreclasificados como críticos
"""
import time
from logging import getLogger

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, recall_score

from app.services.optimizers.base import BaseOptimizer, OptimizerResult

logger = getLogger(__name__)

N_FEATURE_WEIGHTS = 7
N_THRESHOLDS = 3
N_DIMS = N_FEATURE_WEIGHTS + N_THRESHOLDS

FEATURE_NAMES = [
    "heart_rate",
    "spo2",
    "systolic_bp",
    "cholesterol",
    "chest_pain",
    "age",
    "other_risk_factors",
]


def _normalize_features(features: np.ndarray) -> np.ndarray:
    """Normaliza vector de 7 features clínicos a [0, 1] (ya deberían estarlo)."""
    return np.clip(features, 0.0, 1.0)


def _classify_priority(score: float, thresholds: np.ndarray) -> int:
    """Devuelve 0=BAJA, 1=MEDIA, 2=ALTA, 3=CRÍTICA."""
    t_medium, t_high, t_critical = thresholds
    if score >= t_critical:
        return 3
    if score >= t_high:
        return 2
    if score >= t_medium:
        return 1
    return 0


def _fitness(
    weights: np.ndarray,
    thresholds: np.ndarray,
    X: np.ndarray,
    y: np.ndarray,
) -> float:
    """Función objetivo PSO. y ∈ {0,1,2,3}."""
    Xn = _normalize_features(X)
    scores = Xn @ weights
    preds = np.array([_classify_priority(s, thresholds) for s in scores])

    n = max(len(y), 1)
    ordinal_error = float(np.mean(np.abs(preds - y)) / 3.0)

    critical_mask = y == 3
    if critical_mask.sum() > 0:
        critical_fn_rate = float(np.mean(preds[critical_mask] < 3))
    else:
        critical_fn_rate = 0.0

    non_critical_mask = y < 3
    if non_critical_mask.sum() > 0:
        overtriage_rate = float(np.mean(preds[non_critical_mask] == 3))
    else:
        overtriage_rate = 0.0

    return ordinal_error + 3.0 * critical_fn_rate + 0.5 * overtriage_rate


class PSOOptimizer(BaseOptimizer):
    """Particle Swarm Optimization para pesos+umbrales de prioridad clínica."""

    def __init__(
        self,
        n_particles: int = 30,
        max_iter: int = 50,
        w: float = 0.7,
        c1: float = 1.5,
        c2: float = 1.5,
        seed: int = 42,
    ):
        self.n_particles = n_particles
        self.max_iter = max_iter
        self.w = w
        self.c1 = c1
        self.c2 = c2
        self.seed = seed

    def optimize(self, X: np.ndarray, y: np.ndarray) -> OptimizerResult:
        rng = np.random.default_rng(self.seed)
        n_samples, n_features = X.shape
        if n_features != N_FEATURE_WEIGHTS:
            raise ValueError(
                f"PSO espera {N_FEATURE_WEIGHTS} features, recibió {n_features}"
            )
        unique_labels = set(np.unique(y).tolist())
        if not unique_labels.issubset({0, 1, 2, 3}):
            raise ValueError(
                f"PSO espera etiquetas en {{0,1,2,3}}, recibió {sorted(unique_labels)}"
            )

        lb = np.array([0.0] * N_FEATURE_WEIGHTS + [0.10, 0.30, 0.60], dtype=float)
        ub = np.array([1.0] * N_FEATURE_WEIGHTS + [0.40, 0.70, 0.95], dtype=float)

        positions = rng.uniform(lb, ub, size=(self.n_particles, N_DIMS))
        velocities = rng.uniform(-0.1, 0.1, size=(self.n_particles, N_DIMS))

        pbest_positions = positions.copy()
        pbest_fitness = np.full(self.n_particles, np.inf)

        gbest_position = positions[0].copy()
        gbest_fitness = np.inf

        convergence_curve: list[float] = []
        start_time = time.time()

        for iteration in range(self.max_iter):
            for i in range(self.n_particles):
                w_i = positions[i, :N_FEATURE_WEIGHTS]
                t_i = positions[i, N_FEATURE_WEIGHTS:]
                fit = _fitness(w_i, t_i, X, y)
                if fit < pbest_fitness[i]:
                    pbest_fitness[i] = fit
                    pbest_positions[i] = positions[i].copy()
                if fit < gbest_fitness:
                    gbest_fitness = fit
                    gbest_position = positions[i].copy()

            r1 = rng.random((self.n_particles, N_DIMS))
            r2 = rng.random((self.n_particles, N_DIMS))
            velocities = (
                self.w * velocities
                + self.c1 * r1 * (pbest_positions - positions)
                + self.c2 * r2 * (gbest_position - positions)
            )
            positions = np.clip(positions + velocities, lb, ub)

            convergence_curve.append(round(float(gbest_fitness), 6))

        elapsed_ms = int((time.time() - start_time) * 1000)

        opt_weights = gbest_position[:N_FEATURE_WEIGHTS]
        opt_thresholds = np.sort(gbest_position[N_FEATURE_WEIGHTS:])

        Xn = _normalize_features(X)
        scores = Xn @ opt_weights
        preds = np.array([_classify_priority(s, opt_thresholds) for s in scores])

        accuracy_val = float(accuracy_score(y, preds))
        macro_recall = float(recall_score(y, preds, average="macro", zero_division=0))
        f1_val = float(f1_score(y, preds, average="macro", zero_division=0))
        critical_mask = y == 3
        if critical_mask.sum() > 0:
            critical_recall = float(np.mean(preds[critical_mask] == 3))
        else:
            critical_recall = 0.0
        non_critical_mask = y < 3
        if non_critical_mask.sum() > 0:
            overtriage_rate = float(np.mean(preds[non_critical_mask] == 3))
        else:
            overtriage_rate = 0.0
        ordinal_error = float(np.mean(np.abs(preds - y)) / 3.0)

        feature_weights_dict = {name: float(w) for name, w in zip(FEATURE_NAMES, opt_weights)}
        priority_thresholds = [float(t) for t in opt_thresholds]

        metrics = {
            "accuracy": round(accuracy_val, 4),
            "f1_score": round(f1_val, 4),
            "macro_recall": round(macro_recall, 4),
            "critical_recall": round(critical_recall, 4),
            "overtriage_rate": round(overtriage_rate, 4),
            "ordinal_error": round(ordinal_error, 4),
            "fitness": round(float(gbest_fitness), 6),
        }

        logger.info(
            "PSO terminado: fitness=%.4f accuracy=%.3f critical_recall=%.3f iterations=%d runtime=%dms",
            gbest_fitness,
            accuracy_val,
            critical_recall,
            self.max_iter,
            elapsed_ms,
        )

        return OptimizerResult(
            weights=[float(w) for w in opt_weights],
            thresholds=priority_thresholds,
            fitness_history=convergence_curve,
            convergence_curve=convergence_curve,
            best_fitness=round(float(gbest_fitness), 6),
            runtime_ms=elapsed_ms,
            metrics=metrics,
            n_generations=self.max_iter,
            computation_time=round((time.time() - start_time), 3),
            algorithm="PSO",
            version="pso-2026-06-demo",
            priority_thresholds=priority_thresholds,
            feature_weights_dict=feature_weights_dict,
            critical_recall=round(critical_recall, 4),
            overtriage_rate=round(overtriage_rate, 4),
            ordinal_error=round(ordinal_error, 4),
        )
