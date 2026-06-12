import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_predecir(test_client: AsyncClient):
    response = await test_client.post("/predecir", json={
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
    })
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert "risk_level" in data
    assert data["risk_level"] in ("bajo", "medio", "alto")


@pytest.mark.asyncio
async def test_predecir_payload_minimo(test_client: AsyncClient):
    response = await test_client.post("/predecir", json={
        "heart_rate": 72,
    })
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
