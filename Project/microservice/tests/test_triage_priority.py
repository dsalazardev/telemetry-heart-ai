import json
import tempfile
from pathlib import Path

import pytest

from app.services.triage_priority_service import (
    PRIORITY_LABELS,
    TriagePriorityService,
    build_feature_bundle,
)


def test_baseline_priority_thresholds():
    assert TriagePriorityService.baseline_priority(0.0) == 0
    assert TriagePriorityService.baseline_priority(0.39) == 0
    assert TriagePriorityService.baseline_priority(0.40) == 1
    assert TriagePriorityService.baseline_priority(0.69) == 1
    assert TriagePriorityService.baseline_priority(0.70) == 2
    assert TriagePriorityService.baseline_priority(0.84) == 2
    assert TriagePriorityService.baseline_priority(1.0) == 2


def test_build_feature_bundle_normalizes_to_unit_interval():
    bundle = build_feature_bundle(
        heart_rate=120,
        spo2=95,
        systolic_bp=140,
        cholesterol=240,
        chest_pain=2,
        age=50,
        smoker=True,
        previous_condition=False,
    )
    assert len(bundle.values) == 7
    for v in bundle.values:
        assert 0.0 <= v <= 1.0


def test_build_feature_bundle_spo2_inverted():
    low_spo2 = build_feature_bundle(spo2=70)
    high_spo2 = build_feature_bundle(spo2=99)
    assert low_spo2.values[1] > high_spo2.values[1]


def test_service_baseline_when_no_file(tmp_path: Path):
    svc = TriagePriorityService(str(tmp_path / "missing.json"))
    assert svc.loaded is False
    assert svc.version == "baseline"

    bundle = build_feature_bundle(heart_rate=80, spo2=98, age=30)
    result = svc.classify(bundle)
    assert result.priority_label in PRIORITY_LABELS.values()
    assert result.priority_level in (0, 1, 2)
    assert 0.0 <= result.score <= 1.0


def test_service_reload_with_pso_payload(tmp_path: Path):
    weights_file = tmp_path / "weights.json"
    payload = {
        "weights": [0.35, 0.20, 0.25, 0.05, 0.05, 0.05, 0.05],
        "thresholds": [0.30, 0.55],
        "feature_weights_dict": {
            "heart_rate": 0.35,
            "spo2": 0.20,
            "systolic_bp": 0.25,
            "cholesterol": 0.05,
            "chest_pain": 0.05,
            "age": 0.05,
            "other_risk_factors": 0.05,
        },
        "version": "pso-test-2026-06-13",
        "algorithm": "PSO",
        "metrics": {"critical_recall": 0.92, "fitness": 0.18},
    }
    weights_file.write_text(json.dumps(payload), encoding="utf-8")

    svc = TriagePriorityService(str(weights_file))
    assert svc.loaded is True
    assert svc.version == "pso-test-2026-06-13"
    assert svc.thresholds == [0.30, 0.55]
    assert len(svc.feature_names) == 7

    critical_bundle = build_feature_bundle(
        heart_rate=180, spo2=80, systolic_bp=210,
        cholesterol=320, chest_pain=4, age=75,
        smoker=True, previous_condition=True,
    )
    result = svc.classify(critical_bundle)
    assert result.priority_level == 2
    assert result.priority_label == "ALTA"
    assert result.weights_version == "pso-test-2026-06-13"
    assert result.weights_used["heart_rate"] == pytest.approx(0.35)


def test_service_reload_sorts_thresholds(tmp_path: Path):
    weights_file = tmp_path / "weights.json"
    payload = {
        "weights": [0.14] * 7,
        "thresholds": [0.60, 0.30],
        "version": "pso-unsorted",
    }
    weights_file.write_text(json.dumps(payload), encoding="utf-8")

    svc = TriagePriorityService(str(weights_file))
    assert svc.thresholds == [0.30, 0.60]


def test_service_classify_score_in_unit_interval(tmp_path: Path):
    weights_file = tmp_path / "weights.json"
    payload = {
        "weights": [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
        "thresholds": [0.4, 0.6],
        "version": "pso-test",
    }
    weights_file.write_text(json.dumps(payload), encoding="utf-8")

    svc = TriagePriorityService(str(weights_file))
    bundle = build_feature_bundle(
        heart_rate=150, spo2=85, systolic_bp=190,
        cholesterol=280, chest_pain=3, age=65,
        smoker=True, previous_condition=True,
    )
    result = svc.classify(bundle)
    assert 0.0 <= result.score <= 1.0
    assert result.priority_level in (0, 1, 2)


def test_service_rejects_incompatible_11_weights(tmp_path: Path):
    """JSON con 11 weights (RiskEngine legacy) → fallback a baseline.

    Los 11 weights incompatibles (esperamos 7) disparan fallback a baseline
    (defaults con 2 umbrales y pesos uniformes) y ``classify()`` opera.
    """
    weights_file = tmp_path / "weights_legacy.json"
    weights_file.write_text(
        json.dumps({
            "weights": [0.35, 0.45, 0.35, 0.25, 0.20, 0.18, 0.30,
                        0.20, 0.10, 0.12, 0.10],   # 11 weights legacy
            "thresholds": [0.40, 0.70],
            "version": "baseline-v1",
        }),
        encoding="utf-8",
    )

    svc = TriagePriorityService(str(weights_file))

    # 11 weights ≠ 7 → no se cargan, queda en baseline
    assert svc.loaded is False
    assert len(svc.thresholds) == 2
    assert svc.thresholds == [0.40, 0.70]
    assert svc.version == "baseline"

    bundle = build_feature_bundle(heart_rate=160, spo2=82, age=72)
    result = svc.classify(bundle)
    assert result.priority_level in (0, 1, 2)
    assert result.priority_label in ("BAJA", "MEDIA", "ALTA")


def test_risk_engine_and_triage_use_separate_schemas(tmp_path: Path):
    """No-regresión del choque de esquemas: RiskEngine (11 pesos) y
    TriagePriorityService (7 pesos PSO) deben cargar de archivos distintos
    sin pisarse. Antes compartían `weights_path` y el triaje quedaba en
    baseline porque veía 11 pesos != 7.
    """
    from app.services.risk_engine import RiskEngine

    risk_file = tmp_path / "optimized_weights.json"
    risk_file.write_text(json.dumps({
        "weights": [0.1] * 11,
        "thresholds": [0.40, 0.70],
        "bias": -0.5,
        "version": "risk-test",
    }), encoding="utf-8")

    triage_file = tmp_path / "triage_priority_weights.json"
    triage_file.write_text(json.dumps({
        "weights": [0.2] * 7,
        "thresholds": [0.30, 0.55],
        "version": "pso-test",
    }), encoding="utf-8")

    engine = RiskEngine(str(risk_file))
    triage = TriagePriorityService(str(triage_file))

    assert len(engine.weights) == 11
    assert engine.version == "risk-test"
    assert triage.loaded is True
    assert len(triage.weights) == 7
    assert triage.version == "pso-test"


def test_service_drops_legacy_t_critical_when_3_thresholds(tmp_path: Path):
    """JSON legacy 4-niveles (3 umbrales): descarta t_critical y deja 2."""
    weights_file = tmp_path / "weights_legacy4.json"
    weights_file.write_text(
        json.dumps({
            "weights": [0.30, 0.20, 0.15, 0.10, 0.10, 0.10, 0.05],
            "thresholds": [0.40, 0.70, 0.90],
            "version": "pso-legacy4",
        }),
        encoding="utf-8",
    )

    svc = TriagePriorityService(str(weights_file))
    assert svc.loaded is True
    assert svc.thresholds == [0.40, 0.70]
    assert svc.version == "pso-legacy4"

    bundle = build_feature_bundle(
        heart_rate=180, spo2=78, systolic_bp=215,
        cholesterol=320, chest_pain=4, age=75,
        smoker=True, previous_condition=True,
    )
    result = svc.classify(bundle)
    assert result.priority_level in (0, 1, 2)
