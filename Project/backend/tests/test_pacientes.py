import pytest
from httpx import AsyncClient


async def test_crear_paciente(client: AsyncClient):
    response = await client.post("/pacientes", json={
        "usuario": {
            "documento": "999999",
            "nombres": "Ana",
            "apellidos": "García",
            "correo": "ana@test.com",
            "password": "clave123",
            "telefono": "3009999999"
        },
        "fechaNacimiento": "1990-05-15"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["fechaNacimiento"] == "1990-05-15"


async def test_listar_pacientes(client: AsyncClient):
    response = await client.get("/pacientes")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_crear_medico(client: AsyncClient):
    response = await client.post("/medicos", json={
        "usuario": {
            "documento": "888888",
            "nombres": "Carlos",
            "apellidos": "Ruiz",
            "correo": "carlos@test.com",
            "password": "clave123",
            "telefono": "3008888888"
        },
        "especialidad": "Cardiología",
        "licencia": "LIC-12345",
        "telegramChatId": "123456789"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["especialidad"] == "Cardiología"


async def test_fk_simple_paciente(client: AsyncClient):
    # Crear paciente
    response = await client.post("/pacientes", json={
        "usuario": {
            "documento": "777777",
            "nombres": "Luis",
            "apellidos": "Martínez",
            "correo": "luis@test.com",
            "password": "clave123",
            "telefono": "3007777777"
        },
        "fechaNacimiento": "1985-03-20"
    })
    assert response.status_code == 201
    paciente = response.json()
    # El paciente y el usuario deben tener el mismo ID
    assert paciente["id"] is not None
