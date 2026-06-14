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
    assert TriagePriorityService.baseline_priority(0.85) == 3
    assert TriagePriorityService.baseline_priority(1.0) == 3


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
    assert result.priority_level in (0, 1, 2, 3)
    assert 0.0 <= result.score <= 1.0


def test_service_reload_with_pso_payload(tmp_path: Path):
    weights_file = tmp_path / "weights.json"
    payload = {
        "weights": [0.35, 0.20, 0.25, 0.05, 0.05, 0.05, 0.05],
        "thresholds": [0.30, 0.55, 0.70],
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
    assert svc.thresholds == [0.30, 0.55, 0.70]
    assert len(svc.feature_names) == 7

    critical_bundle = build_feature_bundle(
        heart_rate=180, spo2=80, systolic_bp=210,
        cholesterol=320, chest_pain=4, age=75,
        smoker=True, previous_condition=True,
    )
    result = svc.classify(critical_bundle)
    assert result.priority_level == 3
    assert result.priority_label == "CRÍTICA"
    assert result.weights_version == "pso-test-2026-06-13"
    assert result.weights_used["heart_rate"] == pytest.approx(0.35)


def test_service_reload_sorts_thresholds(tmp_path: Path):
    weights_file = tmp_path / "weights.json"
    payload = {
        "weights": [0.14] * 7,
        "thresholds": [0.85, 0.30, 0.60],
        "version": "pso-unsorted",
    }
    weights_file.write_text(json.dumps(payload), encoding="utf-8")

    svc = TriagePriorityService(str(weights_file))
    assert svc.thresholds == [0.30, 0.60, 0.85]


def test_service_classify_score_in_unit_interval(tmp_path: Path):
    weights_file = tmp_path / "weights.json"
    payload = {
        "weights": [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
        "thresholds": [0.4, 0.6, 0.8],
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
    assert result.priority_level in (0, 1, 2, 3)


def test_service_handles_legacy_2_threshold_json(tmp_path: Path):
    """JSON con 2 umbrales y 11 weights (formato 3-niveles legacy).

    Antes del fix, ``classify()`` crasheaba con
    ``ValueError: not enough values to unpack (expected 3, got 2)``.
    Tras el fix, los 11 weights incompatibles disparan fallback a baseline
    (defaults con 3 umbrales y pesos uniformes) y ``classify()`` opera.
    """
    weights_file = tmp_path / "weights_legacy.json"
    weights_file.write_text(
        json.dumps({
            "weights": [0.35, 0.45, 0.35, 0.25, 0.20, 0.18, 0.30,
                        0.20, 0.10, 0.12, 0.10],   # 11 weights legacy
            "thresholds": [0.40, 0.70],            # 2 thresholds legacy
            "version": "baseline-v1",
        }),
        encoding="utf-8",
    )

    svc = TriagePriorityService(str(weights_file))

    # 11 weights ≠ 7 → no se cargan, queda en baseline
    assert svc.loaded is False
    assert len(svc.thresholds) == 3
    assert svc.thresholds == [0.40, 0.70, 0.85]
    assert svc.version == "baseline"

    bundle = build_feature_bundle(heart_rate=160, spo2=82, age=72)
    result = svc.classify(bundle)
    assert result.priority_level in (0, 1, 2, 3)
    assert result.priority_label in ("BAJA", "MEDIA", "ALTA", "CRÍTICA")


def test_service_pads_thresholds_when_only_2(tmp_path: Path):
    """JSON con 7 weights válidos pero 2 umbrales: sintetiza el tercero."""
    weights_file = tmp_path / "weights_partial.json"
    weights_file.write_text(
        json.dumps({
            "weights": [0.30, 0.20, 0.15, 0.10, 0.10, 0.10, 0.05],
            "thresholds": [0.40, 0.70],
            "version": "pso-partial",
        }),
        encoding="utf-8",
    )

    svc = TriagePriorityService(str(weights_file))
    assert svc.loaded is True
    assert len(svc.thresholds) == 3
    assert svc.thresholds[2] >= 0.85
    assert svc.version == "pso-partial"

    bundle = build_feature_bundle(
        heart_rate=180, spo2=78, systolic_bp=215,
        cholesterol=320, chest_pain=4, age=75,
        smoker=True, previous_condition=True,
    )
    result = svc.classify(bundle)
    assert result.priority_level in (0, 1, 2, 3)
