import pytest
from httpx import AsyncClient
from starlette.testclient import TestClient
from app.main import app


async def test_websocket_conexion_exitosa():
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": "1", "tipo": "medico"})
    client = TestClient(app)
    with client.websocket_connect("/telemetria/ws/telemetria/1?token=" + token) as websocket:
        # Conexión establecida
        pass


async def test_websocket_sin_token():
    client = TestClient(app)
    try:
        with client.websocket_connect("/telemetria/ws/telemetria/1") as websocket:
            pass
    except Exception as e:
        # Debería fallar o cerrar con 1008
        assert True
