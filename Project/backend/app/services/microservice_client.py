from typing import Optional
import httpx
from app.core.settings import settings


class MicroserviceClient:
    def __init__(self):
        self.base_url = settings.MICROSERVICE_URL
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    async def solicitar_prediccion(self, datos_lectura: dict) -> dict:
        """
        Envía datos de lectura al microservicio de IA y recibe la predicción.
        datos_lectura debe contener: age, sex, cp, trestbps, chol, fbs,
        restecg, thalach, exang, oldpeak, slope, ca, thal
        """
        try:
            response = await self.client.post("/predict", json=datos_lectura)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"error": "timeout", "status": "timeout_microservicio"}
        except httpx.HTTPStatusError as e:
            return {"error": "http_error", "status_code": e.response.status_code}
        except Exception:
            return {"error": "connection_error", "status": "microservicio_no_disponible"}

    async def close(self):
        await self.client.aclose()


# Singleton para reutilizar
microservice_client = MicroserviceClient()
