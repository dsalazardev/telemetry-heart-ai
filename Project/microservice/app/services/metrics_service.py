"""Métricas para evaluación de priorización clínica (4 niveles).

Calcula accuracy, recall macro, F1, critical_recall, overtriage_rate,
ordinal_error y la fitness de PSO (mismo cálculo que el optimizador).
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, recall_score


def _fitness(ordinal_error: float, critical_fn_rate: float, overtriage_rate: float) -> float:
    return ordinal_error + 3.0 * critical_fn_rate + 0.5 * overtriage_rate


def _priority_metrics(y: np.ndarray, preds: np.ndarray) -> dict:
    n = max(len(y), 1)
    ordinal_error = float(np.mean(np.abs(preds - y)) / 3.0)

    critical_mask = y == 3
    if critical_mask.sum() > 0:
        critical_recall = float(np.mean(preds[critical_mask] == 3))
        critical_fn_rate = float(np.mean(preds[critical_mask] < 3))
    else:
        critical_recall = 0.0
        critical_fn_rate = 0.0

    non_critical_mask = y < 3
    if non_critical_mask.sum() > 0:
        overtriage_rate = float(np.mean(preds[non_critical_mask] == 3))
    else:
        overtriage_rate = 0.0

    fitness = _fitness(ordinal_error, critical_fn_rate, overtriage_rate)

    return {
        "accuracy": float(accuracy_score(y, preds)),
        "f1_score": float(f1_score(y, preds, average="macro", zero_division=0)),
        "macro_recall": float(recall_score(y, preds, average="macro", zero_division=0)),
        "critical_recall": critical_recall,
        "overtriage_rate": overtriage_rate,
        "ordinal_error": ordinal_error,
        "fitness": fitness,
    }


def _classify(scores: np.ndarray, thresholds: list[float]) -> np.ndarray:
    t1, t2, t3 = thresholds
    return np.where(
        scores < t1, 0,
        np.where(scores < t2, 1, np.where(scores < t3, 2, 3)),
    )


def _classify_legacy(scores: np.ndarray, thresholds: list[float]) -> np.ndarray:
    """Compatibilidad con el legacy de 2 umbrales / 3 niveles (baseline)."""
    t1, t2 = thresholds
    return np.where(scores < t1, 0, np.where(scores < t2, 1, 2))


class MetricsService:
    def evaluate(
        self,
        X: np.ndarray,
        y: np.ndarray,
        weights: np.ndarray,
        thresholds: list,
        bias: float = 0.0,
    ) -> dict:
        scores = 1.0 / (1.0 + np.exp(-np.clip(X @ weights + bias, -20, 20)))
        if len(thresholds) == 3:
            preds = _classify(scores, thresholds)
            return _priority_metrics(y, preds)
        preds = _classify_legacy(scores, thresholds)
        legacy = _priority_metrics(y, preds)
        return legacy

    def compare(
        self,
        X: np.ndarray,
        y: np.ndarray,
        baseline_weights: np.ndarray,
        baseline_thresholds: list,
        optimized_weights: np.ndarray,
        optimized_thresholds: list,
        baseline_bias: float = 0.0,
        optimized_bias: float = 0.0,
    ) -> dict:
        base = self.evaluate(X, y, baseline_weights, baseline_thresholds, baseline_bias)
        opt = self.evaluate(X, y, optimized_weights, optimized_thresholds, optimized_bias)
        improvement = {k: round(opt[k] - base[k], 4) for k in base}
        delta = {
            "accuracy": round(opt["accuracy"] - base["accuracy"], 4),
            "critical_recall": round(opt["critical_recall"] - base["critical_recall"], 4),
            "fitness": round(opt["fitness"] - base["fitness"], 4),
            "overtriage_rate": round(opt["overtriage_rate"] - base["overtriage_rate"], 4),
        }
        return {
            "baseline": base,
            "optimized": opt,
            "improvement": improvement,
            "delta": delta,
        }
