import pytest
from httpx import AsyncClient


async def test_login_exitoso(client: AsyncClient, sample_user):
    response = await client.post("/auth/login", json={
        "correo": "juan@test.com",
        "password": "clave123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_fallido(client: AsyncClient):
    response = await client.post("/auth/login", json={
        "correo": "noexiste@test.com",
        "password": "wrong"
    })
    assert response.status_code == 401


async def test_refresh_token(client: AsyncClient, sample_user):
    from app.core.security import create_refresh_token
    refresh = create_refresh_token(data={"sub": str(sample_user.id)})
    response = await client.post("/auth/refresh", json={"refresh_token": refresh})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
