import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_agent_query(test_client: AsyncClient):
    response = await test_client.post("/agent/query", json={
        "question": "What is the risk for a 60 year old male?"
    })
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "tool_used" in data

@pytest.mark.asyncio
async def test_agent_query_empty(test_client: AsyncClient):
    response = await test_client.post("/agent/query", json={"question": ""})
    assert response.status_code == 400
