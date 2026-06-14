"""Demo end-to-end: POST /eventos/{id}/evaluar -> microservicio -> triaje + alerta.

Setup:
  1. Crea un paciente (con su Usuario).
  2. Crea un dispositivo para ese paciente.
  3. Crea un evento.
  4. Registra una telemetria critica.
  5. Asocia la telemetria al evento (UPDATE directo, no hay endpoint).
  6. Llama POST /eventos/{id}/evaluar y muestra la respuesta.

Uso:
    cd Project/backend
    PYTHONPATH=. python scripts/demo_evaluar.py
"""
import asyncio
from datetime import datetime, timezone

import httpx
from sqlalchemy import select, update

from app.core.database import async_session_maker
from app.core.settings import settings
from app.models.dispositivo import Telemetria


BACKEND_URL = "http://localhost:8000"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()

CRITICAL_TELEMETRIA = {
    "frecuenciaCardiaca": 160,
    "spo2": 82,
    "anomaliaEcg": "taquicardia_severa",
    "timestamp": _utcnow_iso(),
}


def _print_step(n: int, label: str) -> None:
    print(f"\n[{n}] {label}")
    print("-" * (len(label) + 6))


def _print_resp(resp: httpx.Response) -> None:
    print(f"  status: {resp.status_code}")
    try:
        body = resp.json()
        for k, v in body.items():
            v_str = str(v)
            if len(v_str) > 120:
                v_str = v_str[:117] + "..."
            print(f"  {k}: {v_str}")
    except Exception:
        print(f"  body: {resp.text[:200]}")


async def _post(client: httpx.AsyncClient, path: str, json: dict) -> httpx.Response:
    print(f"  -> POST {BACKEND_URL}{path}")
    return await client.post(f"{BACKEND_URL}{path}", json=json, timeout=30.0)


async def main() -> None:
    async with httpx.AsyncClient() as client:
        _print_step(1, "Crear paciente")
        resp = await _post(client, "/pacientes", {
            "usuario": {
                "documento": str(int(datetime.now(timezone.utc).timestamp())),
                "nombres": "Demo",
                "apellidos": "Critico",
                "correo": f"demo.critico.{int(datetime.now(timezone.utc).timestamp())}@test.com",
                "password": "demo1234",
                "telefono": "3000000000",
            },
            "fechaNacimiento": "1970-05-15",
        })
        _print_resp(resp)
        if resp.status_code != 201:
            print(f"ERROR: {resp.text}")
            return
        paciente_id = resp.json()["id"]

        _print_step(2, "Crear dispositivo")
        resp = await _post(client, "/dispositivos", {
            "tipo": "wearable",
            "modelo": "DemoWatch 1",
            "sistemaOperativo": "WearOS 4.0",
            "paciente_id": paciente_id,
        })
        _print_resp(resp)
        if resp.status_code not in (200, 201):
            print(f"ERROR: {resp.text}")
            return
        dispositivo_id = resp.json()["id"]

        _print_step(3, "Crear evento")
        ahora = datetime.now(timezone.utc).replace(tzinfo=None)
        ahora_iso = ahora.isoformat()
        resp = await _post(client, "/eventos", {
            "tipo": "telemetria_anomala",
            "ventanaInicio": ahora_iso,
            "ventanaFin": ahora_iso,
        })
        _print_resp(resp)
        if resp.status_code == 500:
            print()
            print("  DIAGNOSTICO: el endpoint /eventos devolvio 500.")
            print("  Posibles causas:")
            print("    - La BD Aiven no respondio (timeout / cold start)")
            print("    - El schema en BD difiere del modelo SQLModel")
            print("    - Revisa los logs del backend uvicorn para el traceback")
            return
        if resp.status_code != 201:
            print(f"ERROR: {resp.text}")
            return
        evento_id = resp.json()["id"]

        _print_step(4, "Registrar telemetria critica")
        telemetria_payload = {**CRITICAL_TELEMETRIA, "dispositivo_id": dispositivo_id}
        resp = await _post(client, "/telemetria", telemetria_payload)
        _print_resp(resp)
        if resp.status_code != 201:
            print(f"ERROR: {resp.text}")
            return
        telemetria_id = resp.json()["id"]

        _print_step(5, f"Asociar telemetria {telemetria_id} al evento {evento_id} (UPDATE directo)")
        async with async_session_maker() as db:
            stmt = update(Telemetria).where(
                Telemetria.id == telemetria_id
            ).values(evento_id=evento_id)
            result = await db.execute(stmt)
            await db.commit()
            print(f"  filas actualizadas: {result.rowcount}")

            check = await db.execute(
                select(Telemetria).where(Telemetria.id == telemetria_id)
            )
            tel = check.scalar_one()
            print(f"  telemetria.evento_id = {tel.evento_id}")

        _print_step(6, f"POST /eventos/{evento_id}/evaluar (consume al microservicio)")
        print(f"  -> POST {BACKEND_URL}/eventos/{evento_id}/evaluar")
        resp = await client.post(
            f"{BACKEND_URL}/eventos/{evento_id}/evaluar", timeout=60.0
        )
        _print_resp(resp)

        if resp.status_code == 200:
            body = resp.json()
            print()
            if body.get("status") == "ok":
                print("  OK triaje + alerta persistidos correctamente")
                print(f"    risk_score        = {body.get('risk_score')}")
                print(f"    risk_level        = {body.get('risk_level')}")
                print(f"    threshold_excd    = {body.get('threshold_exceeded')}")
                if body.get("alerta"):
                    print(f"    alerta.id         = {body['alerta'].get('id')}")
                    print(f"    alerta.tipo       = {body['alerta'].get('tipo')}")
            elif body.get("status") == "error":
                print(f"  X backend devolvio error: {body}")
                print()
                print("  Posibles causas:")
                print("    - El microservicio no esta corriendo (uvicorn en :8001)")
                print("    - Bug conocido: backend no envia Authorization: Bearer al microservicio")
                print("    - El microservicio esta corriendo pero devuelve 401/500")
            else:
                print(f"  ? respuesta no esperada: {body}")
        else:
            print(f"  X HTTP {resp.status_code}: {resp.text}")


if __name__ == "__main__":
    print("=" * 60)
    print("DEMO: POST /eventos/{id}/evaluar (backend -> microservicio)")
    print("=" * 60)
    print(f"BACKEND_URL  = {BACKEND_URL}")
    print(f"DATABASE_URL = {settings.DATABASE_URL_ASYNC[:60]}...")
    print()
    asyncio.run(main())
