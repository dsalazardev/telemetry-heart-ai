"""Motor de riesgo cardiovascular basado en regresión logística con 11 pesos.

Modelo: ``score = sigmoid(Σ(feature_i · weight_i) + bias)``
Salida: score ∈ [0, 1] → nivel bajo/medio/alto según umbrales configurables.

Este esquema es DISTINTO al de ``TriagePriorityService`` (PSO, 7 pesos, modelo
lineal normalizado). Ver README §Arquitectura para la distinción completa.
Los 11 pesos se cargan desde ``optimized_weights.json``; si el archivo no existe
se usan pesos uniformes (baseline-v1).
"""
import json
from logging import getLogger
from pathlib import Path

import numpy as np
import yaml

logger = getLogger(__name__)

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "clinical_params.yaml"


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -20, 20)))


def normalize(value: float | None, low: float, high: float, invert: bool = False) -> float:
    if value is None:
        return 0.0
    norm = np.clip((value - low) / (high - low), 0.0, 1.0)
    return 1.0 - norm if invert else norm


def _load_clinical_config(path: str | Path) -> dict:
    p = Path(path)
    if p.exists():
        # encoding explícito: en Windows open() usa cp1252 por defecto y
        # corrompe los acentos del YAML ("saturación" → "saturaciÃ³n").
        with open(p, encoding="utf-8") as f:
            return yaml.safe_load(f)
    logger.warning("Config %s no encontrado, usando defaults hardcoded", p)
    return {}


CLINICAL_CONFIG = _load_clinical_config(DEFAULT_CONFIG_PATH)


class RiskEngine:
    """Predice riesgo cardiovascular (bajo/medio/alto) con modelo sigmoid 11-pesos.

    Los pesos y umbrales se leen de ``weights_path`` en cada arranque. Si el
    archivo falta, opera en baseline (pesos uniformes, bias -0.5). El método
    ``predict()`` también retorna los ``dominant_factors``: features cuyo
    contribución ponderada supera ``dominant_weight_threshold``.
    """

    def __init__(self, weights_path: str, config: dict | None = None):
        self.config = config or CLINICAL_CONFIG
        self.weights_path = Path(weights_path)
        self.bias = 0.0
        self.weights: np.ndarray | None = None
        self._n_features = 0
        self._load_params()
        self._load_weights()

    def _load_params(self):
        features = self.config.get("features", [])
        self._n_features = len(features)
        self._ordered_keys = [
            (f["name"], f.get("invert", False), f["min"], f["max"])
            for f in features[:7]  # first 7 are physiological with ranges
        ]
        self._factor_names = [f["factor_label"] for f in features]
        self._chest_map = self.config.get("chest_pain_types", {
            "typical_angina": 1.0, "atypical_angina": 2.0,
            "non_anginal": 3.0, "asymptomatic": 4.0,
        })

        thresholds = self.config.get("risk_thresholds", {})
        self.threshold_medium = thresholds.get("medium", 0.40)
        self.threshold_high = thresholds.get("high", 0.70)

        dom = self.config.get("dominant_factor", {})
        self._dominant_weight_threshold = dom.get("weight_threshold", 0.15)
        self._dominant_value_gate = dom.get("value_gate", 0.3)

    def _load_weights(self):
        if self.weights_path.exists():
            try:
                data = json.loads(self.weights_path.read_text())
                self.weights = np.array(data["weights"], dtype=float)
                self._n_features = len(self.weights)
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
        self.weights = np.ones(max(self._n_features, 11), dtype=float) / max(self._n_features, 11)
        self.bias = -0.5
        self.version = "baseline-v1"
        logger.info("Usando baseline (pesos uniformes)")

    def _normalize_features(self, data: dict) -> np.ndarray:
        normalized = []
        for key, invert, low, high in self._ordered_keys:
            normalized.append(normalize(data.get(key), low, high, invert=invert))

        chest_val = self._chest_map.get(data.get("chest_pain_type", ""), 0.0) / max(self._chest_map.values(), default=4.0)
        sex_val = 1.0 if data.get("sex") == "M" else 0.0
        smoker_val = 1.0 if data.get("smoker") else 0.0
        prev_val = 1.0 if data.get("previous_condition") else 0.0
        normalized.extend([chest_val, sex_val, smoker_val, prev_val])

        return np.array(normalized, dtype=float)

    def predict(self, data: dict) -> dict:
        features = self._normalize_features(data)
        score = float(sigmoid(np.dot(features, self.weights) + self.bias))
        level = "bajo" if score < self.threshold_medium else ("medio" if score < self.threshold_high else "alto")
        exceeded = bool(score >= self.threshold_high)

        normed = self._normalize_features(data)
        dominant = [
            self._factor_names[i]
            for i in range(len(normed))
            if normed[i] * self.weights[i] > self._dominant_weight_threshold and normed[i] > self._dominant_value_gate
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
