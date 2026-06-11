import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_healthy(test_client: AsyncClient):
    response = await test_client.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "error"]
    assert "version" in data
    assert "timestamp" in data
