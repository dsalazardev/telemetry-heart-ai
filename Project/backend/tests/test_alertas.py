import pytest
from httpx import AsyncClient


async def test_crear_alerta(client: AsyncClient):
    response = await client.post("/alertas", json={
        "tipo": "anomalia",
        "mensaje": "FC elevada detectada",
        "paciente_id": 1,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["tipo"] == "anomalia"
    assert data["leida"] == False
    assert data["atendida"] == False


async def test_marcar_leida(client: AsyncClient):
    response = await client.post("/alertas", json={
        "tipo": "test",
        "mensaje": "test",
        "paciente_id": 1,
    })
    alerta = response.json()
    response = await client.put(f"/alertas/{alerta['id']}/leer")
    assert response.status_code == 200
    assert response.json()["leida"] == True


async def test_asignar_medico(client: AsyncClient):
    response = await client.post("/alertas", json={
        "tipo": "test",
        "mensaje": "test",
        "paciente_id": 1,
    })
    alerta = response.json()
    response = await client.put(f"/alertas/{alerta['id']}/asignar?medico_id=1")
    assert response.status_code == 200
    assert response.json()["medico_id"] == 1


async def test_atender_alerta(client: AsyncClient):
    response = await client.post("/alertas", json={
        "tipo": "test",
        "mensaje": "test",
        "paciente_id": 1,
    })
    alerta = response.json()
    response = await client.put(f"/alertas/{alerta['id']}/atender")
    assert response.status_code == 200
    assert response.json()["atendida"] == True
    assert response.json()["fechaAtencion"] is not None


async def test_listar_alertas_filtradas(client: AsyncClient):
    response = await client.get("/alertas?atendida=false")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
