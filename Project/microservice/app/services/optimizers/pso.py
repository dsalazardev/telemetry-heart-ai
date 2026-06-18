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
  - 2 umbrales ordenados (∈ [0, 1]):
      7: t_medium
      8: t_high

Función objetivo (minimizar):
  F = ordinal_error
    + 3.0 * top_false_negative_rate
    + 0.5 * overtriage_rate

Donde:
  - ordinal_error          = mean(|pred - y_true|) / 2, ∈ [0, 1]
  - top_FN_rate            = proporción de casos ALTA subclasificados
                             (campo expuesto como `critical_recall` por compat)
  - overtriage_rate        = proporción de no-ALTA sobreclasificados como ALTA
"""
import time
from logging import getLogger

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, recall_score

from app.services.optimizers.base import BaseOptimizer, OptimizerResult

logger = getLogger(__name__)

N_FEATURE_WEIGHTS = 7
N_THRESHOLDS = 2
N_DIMS = N_FEATURE_WEIGHTS + N_THRESHOLDS
TOP_LEVEL = 2  # ALTA: clase de máxima prioridad (3 niveles: 0=BAJA,1=MEDIA,2=ALTA)

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


def _weighted_scores(Xn: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Score por caso, normalizado a [0, 1].

    Debe coincidir con ``TriagePriorityService.classify`` en runtime:
    ``score = sum(f_i * w_i) / sum(|w_i|)``. Sin esta normalización el
    producto punto crudo (hasta ~7) supera cualquier umbral <= 0.95 y todo
    se clasifica como CRÍTICA.
    """
    total_abs = float(np.sum(np.abs(weights))) or 1.0
    return np.clip((Xn @ weights) / total_abs, 0.0, 1.0)


def _classify_priority(score: float, thresholds: np.ndarray) -> int:
    """Devuelve 0=BAJA, 1=MEDIA, 2=ALTA."""
    t_medium, t_high = thresholds
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
    """Función objetivo PSO. y ∈ {0,1,2}."""
    Xn = _normalize_features(X)
    scores = _weighted_scores(Xn, weights)
    preds = np.array([_classify_priority(s, thresholds) for s in scores])

    n = max(len(y), 1)
    ordinal_error = float(np.mean(np.abs(preds - y)) / 2.0)

    critical_mask = y == TOP_LEVEL
    if critical_mask.sum() > 0:
        critical_fn_rate = float(np.mean(preds[critical_mask] < TOP_LEVEL))
    else:
        critical_fn_rate = 0.0

    non_critical_mask = y < TOP_LEVEL
    if non_critical_mask.sum() > 0:
        overtriage_rate = float(np.mean(preds[non_critical_mask] == TOP_LEVEL))
    else:
        overtriage_rate = 0.0

    return ordinal_error + 3.0 * critical_fn_rate + 0.5 * overtriage_rate


class PSOOptimizer(BaseOptimizer):
    """Particle Swarm Optimization para pesos+umbrales de prioridad clínica."""

    # Bounds por defecto de los 2 umbrales ordenados (t_medium, t_high).
    DEFAULT_THRESHOLD_LB = (0.10, 0.40)
    DEFAULT_THRESHOLD_UB = (0.40, 0.85)

    def __init__(
        self,
        n_particles: int = 30,
        max_iter: int = 50,
        w: float = 0.7,
        c1: float = 1.5,
        c2: float = 1.5,
        seed: int = 42,
        threshold_lb: tuple[float, float] | None = None,
        threshold_ub: tuple[float, float] | None = None,
        patience: int | None = None,
        tol: float = 1e-6,
    ):
        """PSO para pesos+umbrales de prioridad clínica.

        Args:
            threshold_lb / threshold_ub: cotas inferior/superior de los 2
                umbrales. Por defecto ``DEFAULT_THRESHOLD_LB/UB``.
            patience: si se especifica, detiene la optimización cuando el
                mejor fitness no mejora más de ``tol`` durante ``patience``
                iteraciones consecutivas (parada temprana). ``None`` = correr
                siempre ``max_iter`` iteraciones.
            tol: mejora mínima para resetear el contador de paciencia.
        """
        self.n_particles = n_particles
        self.max_iter = max_iter
        self.w = w
        self.c1 = c1
        self.c2 = c2
        self.seed = seed
        self.threshold_lb = tuple(threshold_lb or self.DEFAULT_THRESHOLD_LB)
        self.threshold_ub = tuple(threshold_ub or self.DEFAULT_THRESHOLD_UB)
        self.patience = patience
        self.tol = tol

    def optimize(self, X: np.ndarray, y: np.ndarray) -> OptimizerResult:
        rng = np.random.default_rng(self.seed)
        n_samples, n_features = X.shape
        if n_features != N_FEATURE_WEIGHTS:
            raise ValueError(
                f"PSO espera {N_FEATURE_WEIGHTS} features, recibió {n_features}"
            )
        unique_labels = set(np.unique(y).tolist())
        if not unique_labels.issubset({0, 1, 2}):
            raise ValueError(
                f"PSO espera etiquetas en {{0,1,2}}, recibió {sorted(unique_labels)}"
            )

        lb = np.array([0.0] * N_FEATURE_WEIGHTS + list(self.threshold_lb), dtype=float)
        ub = np.array([1.0] * N_FEATURE_WEIGHTS + list(self.threshold_ub), dtype=float)

        positions = rng.uniform(lb, ub, size=(self.n_particles, N_DIMS))
        velocities = rng.uniform(-0.1, 0.1, size=(self.n_particles, N_DIMS))

        pbest_positions = positions.copy()
        pbest_fitness = np.full(self.n_particles, np.inf)

        gbest_position = positions[0].copy()
        gbest_fitness = np.inf

        convergence_curve: list[float] = []
        start_time = time.time()
        iterations_run = 0
        stale_count = 0
        prev_best = np.inf

        for iteration in range(self.max_iter):
            iterations_run = iteration + 1
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

            if self.patience is not None:
                if prev_best - gbest_fitness > self.tol:
                    stale_count = 0
                else:
                    stale_count += 1
                prev_best = gbest_fitness
                if stale_count >= self.patience:
                    logger.info(
                        "PSO parada temprana en iteración %d (sin mejora > %g en %d iters)",
                        iterations_run, self.tol, self.patience,
                    )
                    break

        elapsed_ms = int((time.time() - start_time) * 1000)

        opt_weights = gbest_position[:N_FEATURE_WEIGHTS]
        opt_thresholds = np.sort(gbest_position[N_FEATURE_WEIGHTS:])

        Xn = _normalize_features(X)
        scores = _weighted_scores(Xn, opt_weights)
        preds = np.array([_classify_priority(s, opt_thresholds) for s in scores])

        accuracy_val = float(accuracy_score(y, preds))
        macro_recall = float(recall_score(y, preds, average="macro", zero_division=0))
        f1_val = float(f1_score(y, preds, average="macro", zero_division=0))
        critical_mask = y == TOP_LEVEL
        if critical_mask.sum() > 0:
            critical_recall = float(np.mean(preds[critical_mask] == TOP_LEVEL))
        else:
            critical_recall = 0.0
        non_critical_mask = y < TOP_LEVEL
        if non_critical_mask.sum() > 0:
            overtriage_rate = float(np.mean(preds[non_critical_mask] == TOP_LEVEL))
        else:
            overtriage_rate = 0.0
        ordinal_error = float(np.mean(np.abs(preds - y)) / 2.0)

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
            iterations_run,
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
            n_generations=iterations_run,
            computation_time=round((time.time() - start_time), 3),
            algorithm="PSO",
            version="pso-2026-06-demo",
            priority_thresholds=priority_thresholds,
            feature_weights_dict=feature_weights_dict,
            critical_recall=round(critical_recall, 4),
            overtriage_rate=round(overtriage_rate, 4),
            ordinal_error=round(ordinal_error, 4),
        )
