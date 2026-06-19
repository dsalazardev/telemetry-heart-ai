import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_n8n_webhook_evaluation(test_client: AsyncClient):
    response = await test_client.post("/n8n/webhook", json={
        "paciente_id": 1,
        "dispositivo_id": 5,
        "heart_rate": 150,
        "spo2": 88,
        "systolic_bp": 180,
        "diastolic_bp": 110,
    })
    assert response.status_code == 200
    data = response.json()
    assert "n8n_response" in data
    assert "riesgo" in data["n8n_response"]


@pytest.mark.asyncio
async def test_evaluar_endpoint(test_client: AsyncClient):
    response = await test_client.post("/evaluar", json={
        "paciente_id": 2,
        "frecuenciaCardiaca": 72,
        "spo2": 98,
        "presion_sistolica": 120,
    })
    assert response.status_code == 200
    data = response.json()
    assert "n8n_response" in data
