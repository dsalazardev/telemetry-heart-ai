import pytest
from unittest.mock import AsyncMock, patch
from app.services.microservice_client import MicroserviceClient


@pytest.mark.asyncio
async def test_solicitar_prediccion_exitosa():
    client = MicroserviceClient()
    from unittest.mock import MagicMock
    mock_response = MagicMock()
    mock_response.json = MagicMock(return_value={"probabilidad": 0.85, "clasificacion": "alto", "tiempoMs": 120})
    mock_response.raise_for_status = MagicMock(return_value=None)

    with patch.object(client.client, "post", return_value=mock_response):
        resultado = await client.solicitar_prediccion({"age": 50, "sex": 1, "cp": 2})
        assert resultado["probabilidad"] == 0.85
        assert resultado["clasificacion"] == "alto"


@pytest.mark.asyncio
async def test_solicitar_prediccion_timeout():
    client = MicroserviceClient()
    from httpx import TimeoutException
    with patch.object(client.client, "post", side_effect=TimeoutException("Timeout")):
        resultado = await client.solicitar_prediccion({"age": 50})
        assert resultado["status"] == "timeout_microservicio"


@pytest.mark.asyncio
async def test_solicitar_prediccion_error_conexion():
    client = MicroserviceClient()
    with patch.object(client.client, "post", side_effect=Exception("Connection refused")):
        resultado = await client.solicitar_prediccion({"age": 50})
        assert resultado["status"] == "microservicio_no_disponible"
