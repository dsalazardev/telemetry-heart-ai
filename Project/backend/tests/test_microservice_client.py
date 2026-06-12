import json
import pytest
from unittest.mock import MagicMock, patch
from app.services.microservice_client import MicroserviceClient
from app.schemas.prediccion import PrediccionResponse
from app.schemas.triaje import TriajeCreate


@pytest.mark.asyncio
async def test_solicitar_prediccion_exitosa():
    client = MicroserviceClient()
    mock_response = MagicMock()
    mock_response.json = MagicMock(return_value={
        "risk_score": 0.85,
        "risk_level": "alto",
        "threshold_exceeded": True,
        "dominant_factors": ["factor_1", "factor_2"],
        "clinical_explanation": "test",
        "recommended_action": "intervenir",
        "rag": {"used": True, "sources": []},
        "model": {"technique": "PSO", "weights_version": "v1", "inference_time_ms": 10},
    })
    mock_response.raise_for_status = MagicMock(return_value=None)

    with patch.object(client.client, "post", return_value=mock_response):
        resultado = await client.solicitar_prediccion({"heart_rate": 72})
        assert resultado["risk_score"] == 0.85
        assert resultado["risk_level"] == "alto"


@pytest.mark.asyncio
async def test_solicitar_prediccion_timeout():
    client = MicroserviceClient()
    from httpx import TimeoutException
    with patch.object(client.client, "post", side_effect=TimeoutException("Timeout")):
        resultado = await client.solicitar_prediccion({"heart_rate": 72})
        assert resultado["status"] == "timeout_microservicio"


@pytest.mark.asyncio
async def test_solicitar_prediccion_error_conexion():
    client = MicroserviceClient()
    with patch.object(client.client, "post", side_effect=Exception("Connection refused")):
        resultado = await client.solicitar_prediccion({"heart_rate": 72})
        assert resultado["status"] == "microservicio_no_disponible"


@pytest.mark.asyncio
async def test_solicitar_prediccion_typed_exitosa():
    client = MicroserviceClient()
    mock_response = MagicMock()
    mock_response.json = MagicMock(return_value={
        "risk_score": 0.85,
        "risk_level": "alto",
        "threshold_exceeded": True,
        "dominant_factors": ["factor_1", "factor_2"],
        "clinical_explanation": "test",
        "recommended_action": "intervenir",
        "rag": {"used": True, "sources": []},
        "model": {"technique": "PSO", "weights_version": "v1", "inference_time_ms": 10},
    })
    mock_response.raise_for_status = MagicMock(return_value=None)

    with patch.object(client.client, "post", return_value=mock_response):
        resultado = await client.solicitar_prediccion_typed({"heart_rate": 72})
        assert isinstance(resultado, PrediccionResponse)
        assert resultado.risk_score == 0.85
        assert resultado.risk_level == "alto"


@pytest.mark.asyncio
async def test_solicitar_prediccion_typed_error():
    client = MicroserviceClient()
    from httpx import TimeoutException
    with patch.object(client.client, "post", side_effect=TimeoutException("Timeout")):
        resultado = await client.solicitar_prediccion_typed({"heart_rate": 72})
        assert isinstance(resultado, dict)
        assert resultado["error"] == "timeout"


def test_adaptar_a_triaje():
    client = MicroserviceClient()
    resp = PrediccionResponse(
        risk_score=0.75,
        risk_level="medio",
        threshold_exceeded=True,
        dominant_factors=["factor_1", "factor_2"],
        clinical_explanation="explicación clínica",
        recommended_action="monitorear",
        rag={"used": True, "sources": []},
        model={"technique": "PSO", "weights_version": "v1", "inference_time_ms": 10},
    )
    triaje = client.adaptar_a_triaje(resp, paciente_id=42)
    assert isinstance(triaje, TriajeCreate)
    assert triaje.probabilidadRiesgo == 0.75
    assert triaje.nivelUrgencia == "medio"
    assert triaje.factoresCriticos == '["factor_1", "factor_2"]'
    assert triaje.explicacionClinica == "explicación clínica"
    assert triaje.paciente_id == 42


def test_adaptar_a_alerta_threshold_exceeded():
    client = MicroserviceClient()
    resp = PrediccionResponse(
        risk_score=0.85,
        risk_level="alto",
        threshold_exceeded=True,
        dominant_factors=["fc_elevada"],
        clinical_explanation="test",
        recommended_action="intervención inmediata",
        rag={"used": True, "sources": []},
        model={"technique": "PSO", "weights_version": "v1", "inference_time_ms": 10},
    )
    alerta = client.adaptar_a_alerta(resp, paciente_id=42, triaje_id=1)
    assert alerta is not None
    assert alerta.tipo == "alto"
    assert alerta.mensaje == "intervención inmediata"
    assert alerta.paciente_id == 42
    assert alerta.triaje_id == 1


def test_adaptar_a_alerta_no_threshold():
    client = MicroserviceClient()
    resp = PrediccionResponse(
        risk_score=0.15,
        risk_level="bajo",
        threshold_exceeded=False,
        dominant_factors=["sin factores"],
        clinical_explanation=None,
        recommended_action="monitoreo continuo",
        rag={"used": False, "sources": []},
        model={"technique": "PSO", "weights_version": "v1", "inference_time_ms": 10},
    )
    alerta = client.adaptar_a_alerta(resp, paciente_id=42)
    assert alerta is None
