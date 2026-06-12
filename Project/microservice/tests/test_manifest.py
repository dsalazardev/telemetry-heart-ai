from pathlib import Path

import yaml


def test_manifest_exists():
    path = Path(__file__).parent.parent / "app" / "agents" / "manifest.yaml"
    assert path.exists()


def test_manifest_valid_yaml():
    path = Path(__file__).parent.parent / "app" / "agents" / "manifest.yaml"
    with open(path) as f:
        manifest = yaml.safe_load(f)
    assert "agents" in manifest
    assert "clinical" in manifest["agents"]
    assert "pso" in manifest["agents"]
    assert "n8n" in manifest["agents"]


def test_clinical_params_exists():
    path = Path(__file__).parent.parent / "app" / "config" / "clinical_params.yaml"
    assert path.exists()


def test_clinical_params_valid():
    path = Path(__file__).parent.parent / "app" / "config" / "clinical_params.yaml"
    with open(path) as f:
        cfg = yaml.safe_load(f)
    assert "features" in cfg
    assert "risk_thresholds" in cfg
    assert "n8n_thresholds" in cfg
    assert len(cfg["features"]) >= 7
