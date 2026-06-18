"""Estrategia de priorización basada en un modelo supervisado (RandomForest).

Alternativa *drop-in* a :class:`TriagePriorityService`: expone la misma
interfaz ``classify(FeatureBundle) -> PriorityResult`` para que el resto del
pipeline (``clinical_subgraph``) no cambie. Se selecciona con
``settings.priority_strategy == "ml"``.

El modelo se entrena en ``notebooks/02-baseline.ipynb`` sobre las MISMAS 7
features normalizadas que produce ``build_feature_bundle`` (vía
``pso_tools._load_dataset``), evitando train/serve skew. Predice la prioridad
ordinal de 3 niveles (0=BAJA, 1=MEDIA, 2=ALTA).
"""
from __future__ import annotations

from logging import getLogger
from pathlib import Path

from app.services.triage_priority_service import (
    FEATURE_ORDER,
    PRIORITY_LABELS,
    FeatureBundle,
    PriorityResult,
)

logger = getLogger(__name__)


class MLPriorityService:
    """Clasifica la prioridad de triaje con un RandomForest persistido (.pkl)."""

    def __init__(self, model_path: str | Path):
        self.model_path = Path(model_path)
        self.model = None
        self.version: str = "ml-unloaded"
        self.feature_names: list[str] = list(FEATURE_ORDER)
        self._loaded: bool = False
        self.reload()

    def reload(self) -> None:
        """(Re)carga el modelo desde disco. Tolerante a ausencia del .pkl."""
        if not self.model_path.exists():
            logger.warning(
                "Modelo ML no encontrado en %s; MLPriorityService queda inactivo. "
                "Entrena el modelo con notebooks/02-baseline.ipynb.",
                self.model_path,
            )
            self.model = None
            self._loaded = False
            return
        try:
            import joblib

            self.model = joblib.load(self.model_path)
            self._loaded = True
            self.version = f"rf-ml:{self.model_path.name}"
            logger.info("Modelo ML de prioridad cargado desde %s", self.model_path)
        except Exception as exc:  # noqa: BLE001 — degradar a inactivo, no romper boot
            logger.error("No se pudo cargar el modelo ML %s: %s", self.model_path, exc)
            self.model = None
            self._loaded = False

    @property
    def loaded(self) -> bool:
        return self._loaded

    def classify(self, features: FeatureBundle) -> PriorityResult:
        """Predice la prioridad 0/1/2 a partir del bundle de 7 features.

        Mantiene la firma de ``TriagePriorityService.classify`` para ser
        intercambiable. El ``score`` se deriva de ``predict_proba`` como una
        esperanza ordinal normalizada (∈ [0, 1]) para conservar semántica
        comparable con el scoring ponderado del PSO.
        """
        if not self._loaded or self.model is None:
            raise RuntimeError(
                "MLPriorityService no tiene modelo cargado; "
                f"verifica {self.model_path}"
            )

        x = [features.as_array()]
        level = int(self.model.predict(x)[0])
        level = max(0, min(2, level))

        score = self._ordinal_score(x)

        importances = self._feature_importances()

        return PriorityResult(
            score=round(score, 4),
            priority_label=PRIORITY_LABELS[level],
            priority_level=level,
            weights_used=importances,
            weights_version=self.version,
        )

    def _ordinal_score(self, x: list[list[float]]) -> float:
        """Esperanza ordinal E[level]/2 ∈ [0,1] si hay predict_proba; si no, level/2."""
        proba_fn = getattr(self.model, "predict_proba", None)
        classes = getattr(self.model, "classes_", None)
        if proba_fn is not None and classes is not None:
            proba = proba_fn(x)[0]
            expected = sum(float(c) * float(p) for c, p in zip(classes, proba))
            return max(0.0, min(1.0, expected / 2.0))
        level = int(self.model.predict(x)[0])
        return max(0.0, min(1.0, level / 2.0))

    def _feature_importances(self) -> dict[str, float]:
        importances = getattr(self.model, "feature_importances_", None)
        if importances is None:
            return {}
        return {
            name: float(w)
            for name, w in zip(self.feature_names, importances)
        }
