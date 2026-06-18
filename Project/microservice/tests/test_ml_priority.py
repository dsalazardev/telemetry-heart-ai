from pathlib import Path

import joblib
import numpy as np
import pytest
from sklearn.ensemble import RandomForestClassifier

from app.services.ml_priority_service import MLPriorityService
from app.services.triage_priority_service import PRIORITY_LABELS, build_feature_bundle


def _train_tiny_model(path: Path) -> None:
    """Entrena un RF minimo sobre 7 features (espacio del bundle) -> 3 clases."""
    rng = np.random.default_rng(42)
    X = rng.random((60, 7))
    # Etiqueta ordinal proporcional a la media de las features (separable).
    y = np.clip((X.mean(axis=1) * 3).astype(int), 0, 2)
    model = RandomForestClassifier(n_estimators=10, random_state=42).fit(X, y)
    joblib.dump(model, path)


def test_inactive_when_model_missing(tmp_path: Path):
    svc = MLPriorityService(str(tmp_path / "no_model.pkl"))
    assert svc.loaded is False
    with pytest.raises(RuntimeError):
        svc.classify(build_feature_bundle(heart_rate=80, spo2=98, age=30))


def test_loads_and_classifies(tmp_path: Path):
    model_path = tmp_path / "model.pkl"
    _train_tiny_model(model_path)

    svc = MLPriorityService(str(model_path))
    assert svc.loaded is True
    assert svc.version.startswith("rf-ml:")

    result = svc.classify(
        build_feature_bundle(
            heart_rate=160, spo2=82, systolic_bp=200,
            cholesterol=320, chest_pain=4, age=75,
            smoker=True, previous_condition=True,
        )
    )
    assert result.priority_level in (0, 1, 2)
    assert result.priority_label in PRIORITY_LABELS.values()
    assert 0.0 <= result.score <= 1.0
    assert result.weights_version == svc.version
    # feature_importances expuestos como weights_used (7 features del bundle).
    assert set(result.weights_used) == {
        "heart_rate", "spo2", "systolic_bp", "cholesterol",
        "chest_pain", "age", "other_risk_factors",
    }


def test_interface_matches_triage_service(tmp_path: Path):
    """MLPriorityService es drop-in: misma firma classify(bundle)->PriorityResult."""
    model_path = tmp_path / "model.pkl"
    _train_tiny_model(model_path)
    svc = MLPriorityService(str(model_path))

    bundle = build_feature_bundle(heart_rate=70, spo2=99, age=30)
    result = svc.classify(bundle)
    # Campos canonicos de PriorityResult.
    assert hasattr(result, "score")
    assert hasattr(result, "priority_label")
    assert hasattr(result, "priority_level")
    assert hasattr(result, "weights_used")
    assert hasattr(result, "weights_version")
