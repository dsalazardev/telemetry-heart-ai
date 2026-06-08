import time
from logging import getLogger

import numpy as np
from sklearn.metrics import f1_score, recall_score

from app.services.optimizers.base import BaseOptimizer, OptimizerResult

logger = getLogger(__name__)


def _fitness(weights: np.ndarray, thresholds: np.ndarray, bias: float, X: np.ndarray, y: np.ndarray) -> float:
    scores = 1.0 / (1.0 + np.exp(-np.clip(X @ weights + bias, -20, 20)))
    preds = np.where(scores < thresholds[0], 0, np.where(scores < thresholds[1], 1, 2))
    high_risk = y == 2
    pred_high = preds == 2
    tp = np.sum(high_risk & pred_high)
    fn = np.sum(high_risk & ~pred_high)
    fp = np.sum(~high_risk & pred_high)
    fnr = fn / max(tp + fn, 1)
    recall = tp / max(tp + fn, 1)
    f1 = f1_score(y, preds, average="macro", zero_division=0)
    fpr = fp / max(fp + np.sum(~high_risk & ~pred_high), 1)
    return 0.45 * fnr + 0.25 * (1 - recall) + 0.20 * (1 - f1) + 0.10 * fpr


class PSOOptimizer(BaseOptimizer):
    def __init__(self, n_particles: int = 30, max_iter: int = 100, w: float = 0.7, c1: float = 1.5, c2: float = 1.5):
        self.n_particles = n_particles
        self.max_iter = max_iter
        self.w = w
        self.c1 = c1
        self.c2 = c2
        self._fitness_history: list[float] = []

    def optimize(self, X: np.ndarray, y: np.ndarray) -> OptimizerResult:
        n_features = X.shape[1]
        n_dims = n_features + 3

        lb = np.array([0.0] * n_features + [0.0, 0.0, -1.0])
        ub = np.array([1.0] * n_features + [1.0, 1.0, 1.0])

        positions = np.random.uniform(lb, ub, (self.n_particles, n_dims))
        velocities = np.random.uniform(-0.1, 0.1, (self.n_particles, n_dims))

        pbest = positions.copy()
        pbest_fitness = np.full(self.n_particles, np.inf)
        gbest = positions[0].copy()
        gbest_fitness = np.inf

        start_time = time.time()

        for iteration in range(self.max_iter):
            for i in range(self.n_particles):
                w_part = positions[i, :n_features]
                thresholds = positions[i, n_features:n_features + 2]
                bias = positions[i, n_features + 2]
                fit = _fitness(w_part, thresholds, bias, X, y)
                if fit < pbest_fitness[i]:
                    pbest_fitness[i] = fit
                    pbest[i] = positions[i].copy()
                if fit < gbest_fitness:
                    gbest_fitness = fit
                    gbest = positions[i].copy()

            r1 = np.random.random((self.n_particles, n_dims))
            r2 = np.random.random((self.n_particles, n_dims))
            velocities = (
                self.w * velocities
                + self.c1 * r1 * (pbest - positions)
                + self.c2 * r2 * (gbest - positions)
            )
            positions = np.clip(positions + velocities, lb, ub)

            self._fitness_history.append(gbest_fitness)

        elapsed = time.time() - start_time

        w_opt = gbest[:n_features].tolist()
        thresholds_opt = gbest[n_features:n_features + 2].tolist()
        bias_opt = float(gbest[n_features + 2])

        scores = 1.0 / (1.0 + np.exp(-np.clip(X @ gbest[:n_features] + bias_opt, -20, 20)))
        preds = np.where(scores < thresholds_opt[0], 0, np.where(scores < thresholds_opt[1], 1, 2))
        high_risk = y == 2
        pred_high = preds == 2
        tp = int(np.sum(high_risk & pred_high))
        fn = int(np.sum(high_risk & ~pred_high))
        recall_val = float(recall_score(y, preds, average="macro", zero_division=0))
        f1_val = float(f1_score(y, preds, average="macro", zero_division=0))

        return OptimizerResult(
            weights=w_opt,
            thresholds=thresholds_opt,
            bias=bias_opt,
            fitness_history=self._fitness_history,
            metrics={
                "recall_high_risk": recall_val,
                "false_negative_rate": fn / max(tp + fn, 1),
                "f1_score": f1_val,
            },
            n_generations=self.max_iter,
            computation_time=round(elapsed, 3),
            algorithm="PSO",
            version="2026-06-demo-v1",
        )
