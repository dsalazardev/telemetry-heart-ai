import json
from logging import getLogger
from pathlib import Path

import numpy as np

logger = getLogger(__name__)

CLINICAL_RANGES = {
    "heart_rate": (30, 220),
    "spo2": (60, 100),
    "systolic_bp": (60, 260),
    "diastolic_bp": (30, 160),
    "cholesterol": (100, 400),
    "glucose": (50, 350),
    "age": (0, 120),
}

DOMINANT_FACTOR_THRESHOLD = 0.15


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -20, 20)))


def normalize(value: float | None, low: float, high: float, invert: bool = False) -> float:
    if value is None:
        return 0.0
    norm = np.clip((value - low) / (high - low), 0.0, 1.0)
    return 1.0 - norm if invert else norm


class RiskEngine:
    def __init__(self, weights_path: str):
        self.weights_path = Path(weights_path)
        self.bias = 0.0
        self.weights: np.ndarray | None = None
        self.threshold_medium: float = 0.40
        self.threshold_high: float = 0.70
        self.version: str = "baseline-v1"
        self._load_weights()

    def _load_weights(self):
        if self.weights_path.exists():
            try:
                data = json.loads(self.weights_path.read_text())
                self.weights = np.array(data["weights"], dtype=float)
                if "thresholds" in data:
                    self.threshold_medium = data["thresholds"][0]
                    self.threshold_high = data["thresholds"][1]
                if "bias" in data:
                    self.bias = data["bias"]
                self.version = data.get("version", "unknown")
                logger.info("Pesos cargados: versión %s", self.version)
                return
            except Exception as e:
                logger.error("Error cargando pesos: %s", e)
        self.weights = np.ones(11, dtype=float) / 11.0
        self.bias = -0.5
        logger.info("Usando baseline (pesos uniformes)")

    def _normalize_features(self, data: dict) -> np.ndarray:
        ordered_keys = [
            ("heart_rate", False),
            ("spo2", True),
            ("systolic_bp", False),
            ("diastolic_bp", False),
            ("cholesterol", False),
            ("glucose", False),
            ("age", False),
        ]
        normalized = []
        for key, invert in ordered_keys:
            low, high = CLINICAL_RANGES[key]
            normalized.append(normalize(data.get(key), low, high, invert=invert))
        sex_val = 1.0 if data.get("sex") == "M" else 0.0
        smoker_val = 1.0 if data.get("smoker") else 0.0
        prev_val = 1.0 if data.get("previous_condition") else 0.0
        chest_map = {"typical_angina": 1.0, "atypical_angina": 2.0, "non_anginal": 3.0, "asymptomatic": 4.0}
        chest_val = chest_map.get(data.get("chest_pain_type", ""), 0.0) / 4.0
        normalized.extend([chest_val, sex_val, smoker_val, prev_val])
        return np.array(normalized, dtype=float)

    def predict(self, data: dict) -> dict:
        features = self._normalize_features(data)
        score = float(sigmoid(np.dot(features, self.weights) + self.bias))
        level = "bajo" if score < self.threshold_medium else ("medio" if score < self.threshold_high else "alto")
        exceeded = bool(score >= self.threshold_high)

        factor_names = [
            "frecuencia cardiaca elevada",
            "saturación baja",
            "presión sistólica elevada",
            "presión diastólica elevada",
            "colesterol elevado",
            "glucosa elevada",
            "edad avanzada",
            "dolor torácico asintomático",
            "sexo masculino",
            "tabaquismo",
            "condición previa",
        ]
        normed = self._normalize_features(data)
        dominant = [
            factor_names[i]
            for i in range(len(normed))
            if normed[i] * self.weights[i] > DOMINANT_FACTOR_THRESHOLD and normed[i] > 0.3
        ]
        if not dominant:
            dominant = ["sin factores dominantes significativos"]

        return {
            "risk_score": round(float(score), 4),
            "risk_level": level,
            "threshold_exceeded": exceeded,
            "dominant_factors": dominant,
            "recommended_action": "Generar alerta prioritaria y solicitar revisión médica."
            if exceeded
            else "Monitoreo continuo sin intervención inmediata.",
        }
