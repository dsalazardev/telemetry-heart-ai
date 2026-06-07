import pytest
from httpx import AsyncClient


async def test_telemetria_valida(client: AsyncClient):
    # Crear dispositivo primero (necesita paciente)
    response = await client.post("/pacientes", json={
        "usuario": {
            "documento": "111111",
            "nombres": "Pedro",
            "apellidos": "López",
            "correo": "pedro@test.com",
            "password": "clave123",
            "telefono": "3001111111"
        },
        "fechaNacimiento": "1995-01-01"
    })
    paciente = response.json()

    response = await client.post("/dispositivos", json={
        "tipo": "WearOS",
        "modelo": "Galaxy Watch 5",
        "sistemaOperativo": "Wear OS 3",
        "paciente_id": paciente["id"]
    })
    dispositivo = response.json()

    response = await client.post("/telemetria", json={
        "frecuenciaCardiaca": 72.0,
        "spo2": 98.0,
        "timestamp": "2026-06-07T10:00:00",
        "dispositivo_id": dispositivo["id"]
    })
    assert response.status_code == 201
    data = response.json()
    assert data["frecuenciaCardiaca"] == 72.0
    assert data["estadoProcesamiento"] == "validada"


async def test_telemetria_rango_invalido(client: AsyncClient):
    # Crear paciente y dispositivo
    response = await client.post("/pacientes", json={
        "usuario": {
            "documento": "222222",
            "nombres": "María",
            "apellidos": "Gómez",
            "correo": "maria@test.com",
            "password": "clave123",
            "telefono": "3002222222"
        },
        "fechaNacimiento": "1992-02-02"
    })
    paciente = response.json()
    response = await client.post("/dispositivos", json={
        "tipo": "WearOS",
        "modelo": "Galaxy Watch 5",
        "sistemaOperativo": "Wear OS 3",
        "paciente_id": paciente["id"]
    })
    dispositivo = response.json()

    response = await client.post("/telemetria", json={
        "frecuenciaCardiaca": 300.0,
        "spo2": 98.0,
        "timestamp": "2026-06-07T10:00:00",
        "dispositivo_id": dispositivo["id"]
    })
    assert response.status_code == 422
