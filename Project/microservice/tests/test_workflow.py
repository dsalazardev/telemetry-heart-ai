import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_workflow_trigger(test_client: AsyncClient):
    response = await test_client.post("/workflow/trigger", json={
        "adapter_id": 1,
        "payload": {"test": "data"}
    })
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
