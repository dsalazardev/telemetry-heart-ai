import pytest
from httpx import AsyncClient


async def test_crear_evento(client: AsyncClient):
    response = await client.post("/eventos", json={
        "tipo": "reporte_periodico",
        "ventanaInicio": "2026-06-07T10:00:00",
        "ventanaFin": "2026-06-07T10:05:00",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["tipo"] == "reporte_periodico"


async def test_evaluar_umbral(client: AsyncClient):
    # Crear evento
    response = await client.post("/eventos", json={
        "tipo": "reporte_periodico",
        "ventanaInicio": "2026-06-07T10:00:00",
        "ventanaFin": "2026-06-07T10:05:00",
    })
    evento = response.json()

    response = await client.post(f"/eventos/{evento['id']}/evaluar")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
