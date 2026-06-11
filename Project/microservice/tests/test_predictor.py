import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_predict_valid(test_client: AsyncClient):
    response = await test_client.post("/predict/", json={
        "age": 60, "sex": 1, "cp": 0, "trestbps": 130,
        "chol": 240, "fbs": False, "restecg": 1, "thalach": 140,
        "exang": False, "oldpeak": 2.0, "slope": 1, "ca": 0, "thal": 2
    })
    assert response.status_code == 200
    data = response.json()
    assert "probabilidad" in data
    assert "clasificacion" in data
    assert data["clasificacion"] in ["bajo", "medio", "alto"]

@pytest.mark.asyncio
async def test_predict_invalid(test_client: AsyncClient):
    response = await test_client.post("/predict/", json={
        "age": 60, "sex": 1  # Missing features
    })
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_health(test_client: AsyncClient):
    response = await test_client.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "error"]
    assert "dependencies" in data
