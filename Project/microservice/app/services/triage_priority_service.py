"""Servicio runtime de priorización clínica (4 niveles: BAJA/MEDIA/ALTA/CRÍTICA).

Carga `optimized_weights.json` (7 pesos + 3 umbrales producidos por PSO) y aplica
el clasificador al vector de features normalizado.

Responsabilidad única:
  1. Normalizar 7 features clínicos a [0, 1].
  2. Calcular score = sum(w_i * feature_i) / sum(|w_i|).
  3. Clasificar en 0/1/2/3 según umbrales PSO.

Cero dependencias de FastAPI, LangChain, Chroma o LLM.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path

logger = getLogger(__name__)

FEATURE_ORDER: list[str] = [
    "heart_rate",
    "spo2",
    "systolic_bp",
    "cholesterol",
    "chest_pain",
    "age",
    "other_risk_factors",
]

PRIORITY_LABELS: dict[int, str] = {
    0: "BAJA",
    1: "MEDIA",
    2: "ALTA",
    3: "CRÍTICA",
}


@dataclass(frozen=True)
class PriorityResult:
    score: float
    priority_label: str
    priority_level: int
    weights_used: dict[str, float]
    weights_version: str


@dataclass(frozen=True)
class FeatureBundle:
    """Features clínicos ya normalizados a [0, 1] en el orden canónico."""

    values: list[float]

    def as_array(self) -> list[float]:
        return list(self.values)


def build_feature_bundle(
    heart_rate: float | None = None,
    spo2: float | None = None,
    systolic_bp: float | None = None,
    cholesterol: float | None = None,
    chest_pain: float | None = None,
    age: float | None = None,
    smoker: bool | None = None,
    previous_condition: bool | None = None,
) -> FeatureBundle:
    """Normaliza features crudos al espacio [0, 1] y al orden canónico.

    Rangos (lineal, clamp):
      heart_rate    30-220  → (x-30)/190
      spo2          60-100  → 1 - (x-60)/40   (invert: bajo=peor)
      systolic_bp   60-260  → (x-60)/200
      cholesterol   100-400 → (x-100)/300
      chest_pain    0-4     → x/4
      age           0-120   → x/120
      other_risk    promedio(smoker, previous_condition) ∈ {0, 0.5, 1}
    """
    def _scale(v: float | None, lo: float, hi: float, invert: bool = False) -> float:
        if v is None:
            return 0.0
        norm = max(0.0, min(1.0, (v - lo) / (hi - lo)))
        return 1.0 - norm if invert else norm

    values = [
        _scale(heart_rate, 30, 220),
        _scale(spo2, 60, 100, invert=True),
        _scale(systolic_bp, 60, 260),
        _scale(cholesterol, 100, 400),
        _scale(chest_pain, 0, 4),
        _scale(age, 0, 120),
        (
            (1.0 if smoker else 0.0) + (1.0 if previous_condition else 0.0)
        ) / 2.0,
    ]
    return FeatureBundle(values=values)


class TriagePriorityService:
    """Aplica pesos+umbrales PSO al vector de features y devuelve la prioridad.

    Si `weights_path` no existe o está malformado, opera en modo baseline
    (3 niveles derivados de `risk_score`). El método `reload()` permite
    hot-swap tras un upload vía `POST /optimize`.
    """

    def __init__(self, weights_path: str | Path):
        self.weights_path = Path(weights_path)
        self.weights: list[float] = [1.0 / 7.0] * 7
        self.thresholds: list[float] = [0.40, 0.70, 0.85]
        self.version: str = "baseline"
        self.feature_names: list[str] = list(FEATURE_ORDER)
        self._loaded: bool = False
        self.reload()

    def reload(self) -> None:
        """Recarga pesos desde disco. No-op silencioso si el archivo no existe.

        Tolerancia de esquema:
          - ``thresholds`` con 2 valores (legacy 3-niveles) → sintetiza un
            ``t_critical`` a ``max(0.85, t_high + 0.10)``.
          - ``weights`` con ≠ 7 dimensiones (legacy 11-features u otro) →
            rechaza silenciosamente y mantiene los defaults baseline.
        """
        if not self.weights_path.exists():
            logger.warning(
                "No se encontraron pesos PSO en %s; usando baseline 3-niveles",
                self.weights_path,
            )
            self._loaded = False
            return

        try:
            data = json.loads(self.weights_path.read_text(encoding="utf-8"))
            weights_raw = [float(w) for w in data["weights"]]
            thresholds_raw = [float(t) for t in data["thresholds"]]

            if len(thresholds_raw) == 2:
                synthesized = max(0.85, thresholds_raw[1] + 0.10)
                thresholds_raw.append(synthesized)
                logger.info(
                    "JSON legacy detectado (2 umbrales); t_critical sintetizado a %.2f",
                    synthesized,
                )
            elif len(thresholds_raw) != 3:
                logger.error(
                    "Se esperaban 3 umbrales (o 2 legacy), se encontraron %d",
                    len(thresholds_raw),
                )
                self._loaded = False
                return
            thresholds_raw.sort()

            if len(weights_raw) != 7:
                logger.warning(
                    "Pesos PSO con %d dimensiones (esperaba 7). Manteniendo baseline.",
                    len(weights_raw),
                )
                self._loaded = False
                return

            self.weights = weights_raw
            self.thresholds = thresholds_raw
            self.version = str(data.get("version", "pso-unknown"))

            feature_dict = data.get("feature_weights_dict")
            if isinstance(feature_dict, dict) and len(feature_dict) == 7:
                self.feature_names = list(feature_dict.keys())
            self._loaded = True
            logger.info(
                "TriagePriorityService recargado: version=%s weights=%d thresholds=%s",
                self.version,
                len(self.weights),
                self.thresholds,
            )
        except Exception as e:
            logger.error("Error cargando pesos PSO (%s): usando baseline", e)
            self._loaded = False

    @property
    def loaded(self) -> bool:
        return self._loaded

    def classify(self, features: FeatureBundle) -> PriorityResult:
        if not features or len(features.values) != 7:
            raise ValueError(
                f"FeatureBundle debe tener 7 valores, recibió {len(features.values) if features else 0}"
            )

        weights = self.weights[:7]
        total_abs = sum(abs(w) for w in weights) or 1.0
        score = sum(f * w for f, w in zip(features.values, weights)) / total_abs
        score = max(0.0, min(1.0, score))

        t_medium, t_high, t_critical = self.thresholds
        if score >= t_critical:
            level = 3
        elif score >= t_high:
            level = 2
        elif score >= t_medium:
            level = 1
        else:
            level = 0

        weights_dict = {name: float(w) for name, w in zip(self.feature_names, weights)}
        return PriorityResult(
            score=round(score, 4),
            priority_label=PRIORITY_LABELS[level],
            priority_level=level,
            weights_used=weights_dict,
            weights_version=self.version,
        )

    @staticmethod
    def baseline_priority(risk_score: float) -> int:
        """Baseline 3-niveles (Nivel 2) usado como referencia comparativa.

        Riesgo ≥ 0.85  → 3 (CRÍTICA)
        Riesgo ≥ 0.70  → 2 (ALTA)
        Riesgo ≥ 0.40  → 1 (MEDIA)
        Resto          → 0 (BAJA)
        """
        if risk_score >= 0.85:
            return 3
        if risk_score >= 0.70:
            return 2
        if risk_score >= 0.40:
            return 1
        return 0
