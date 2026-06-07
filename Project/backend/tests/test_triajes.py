import pytest
from httpx import AsyncClient


async def test_crear_triaje(client: AsyncClient):
    response = await client.post("/triajes", json={
        "probabilidadRiesgo": 0.85,
        "nivelUrgencia": "alto",
        "factoresCriticos": "FC elevada",
        "explicacionClinica": "Riesgo cardiovascular alto",
        "paciente_id": 1,
        "medico_id": 1
    })
    assert response.status_code == 201
    data = response.json()
    assert data["nivelUrgencia"] == "alto"
    assert data["atendida"] == False


async def test_listar_pendientes(client: AsyncClient):
    response = await client.get("/triajes/pendientes")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_atender_triaje(client: AsyncClient):
    # Crear triaje
    response = await client.post("/triajes", json={
        "probabilidadRiesgo": 0.5,
        "nivelUrgencia": "medio",
        "paciente_id": 1,
    })
    triaje = response.json()
    # Atender
    response = await client.put(f"/triajes/{triaje['id']}/atender?medico_id=1")
    assert response.status_code == 200
    data = response.json()
    assert data["atendida"] == True


async def test_logs_triaje(client: AsyncClient):
    # Crear triaje
    response = await client.post("/triajes", json={
        "probabilidadRiesgo": 0.2,
        "nivelUrgencia": "bajo",
        "paciente_id": 1,
    })
    triaje = response.json()
    response = await client.get(f"/triajes/{triaje['id']}/logs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
