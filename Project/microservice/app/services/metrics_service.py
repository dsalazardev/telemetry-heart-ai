import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, recall_score


class MetricsService:
    def evaluate(self, X: np.ndarray, y: np.ndarray, weights: np.ndarray, thresholds: list, bias: float = 0.0) -> dict:
        scores = 1.0 / (1.0 + np.exp(-np.clip(X @ weights + bias, -20, 20)))
        preds = np.where(scores < thresholds[0], 0, np.where(scores < thresholds[1], 1, 2))
        high_risk = y == 2
        pred_high = preds == 2
        tp = int(np.sum(high_risk & pred_high))
        fn = int(np.sum(high_risk & ~pred_high))
        fp = int(np.sum(~high_risk & pred_high))
        return {
            "accuracy": float(accuracy_score(y, preds)),
            "recall_high_risk": float(recall_score(y, preds, average="macro", zero_division=0)),
            "false_negative_rate": fn / max(tp + fn, 1),
            "f1_score": float(f1_score(y, preds, average="macro", zero_division=0)),
        }

    def compare(self, X: np.ndarray, y: np.ndarray, baseline_weights: np.ndarray, baseline_thresholds: list,
                optimized_weights: np.ndarray, optimized_thresholds: list, baseline_bias: float = 0.0, optimized_bias: float = 0.0) -> dict:
        base = self.evaluate(X, y, baseline_weights, baseline_thresholds, baseline_bias)
        opt = self.evaluate(X, y, optimized_weights, optimized_thresholds, optimized_bias)
        improvement = {
            k: round(opt[k] - base[k], 4) for k in base
        }
        delta = {
            "accuracy": round(opt["accuracy"] - base["accuracy"], 4),
            "recall_high_risk": round(opt["recall_high_risk"] - base["recall_high_risk"], 4),
            "f1": round(opt["f1_score"] - base["f1_score"], 4),
        }
        return {
            "baseline": base,
            "optimized": opt,
            "improvement": improvement,
            "delta": delta,
        }
