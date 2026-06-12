import pytest
from app.services.risk_engine import RiskEngine


@pytest.fixture
def engine():
    return RiskEngine("app/data/optimized_weights.json")


PACIENTE_SANO = {
    "heart_rate": 72,
    "spo2": 98,
    "systolic_bp": 118,
    "diastolic_bp": 76,
    "cholesterol": 180,
    "glucose": 90,
    "age": 35,
    "sex": "F",
    "smoker": False,
    "previous_condition": False,
}

PACIENTE_CRITICO = {
    "heart_rate": 160,
    "spo2": 82,
    "systolic_bp": 200,
    "diastolic_bp": 120,
    "cholesterol": 300,
    "glucose": 250,
    "age": 72,
    "sex": "M",
    "chest_pain_type": "asymptomatic",
    "smoker": True,
    "previous_condition": True,
}


def test_paciente_sano_riesgo_bajo(engine):
    result = engine.predict(PACIENTE_SANO)
    assert result["risk_level"] == "bajo"
    assert result["threshold_exceeded"] is False
    assert result["risk_score"] < 0.4


def test_paciente_critico_riesgo_alto(engine):
    result = engine.predict(PACIENTE_CRITICO)
    assert result["risk_level"] == "alto"
    assert result["threshold_exceeded"] is True
    assert result["risk_score"] >= 0.7


def test_datos_incompletos(engine):
    data = {"heart_rate": 138, "spo2": 91}
    result = engine.predict(data)
    assert "risk_score" in result
    assert result["risk_level"] in ("bajo", "medio", "alto")


def test_factores_dominantes(engine):
    result = engine.predict(PACIENTE_CRITICO)
    assert len(result["dominant_factors"]) > 0


def test_recomendacion_critico(engine):
    result = engine.predict(PACIENTE_CRITICO)
    assert "alerta prioritaria" in result["recommended_action"].lower()


def test_recomendacion_sano(engine):
    result = engine.predict(PACIENTE_SANO)
    assert "monitoreo continuo" in result["recommended_action"].lower()
