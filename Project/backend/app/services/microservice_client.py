import json
from typing import Optional
import httpx
from app.core.settings import settings
from app.schemas.prediccion import PrediccionResponse
from app.schemas.triaje import TriajeCreate
from app.schemas.alerta import AlertaCreate


class MicroserviceClient:
    def __init__(self):
        self.base_url = settings.MICROSERVICE_URL
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    async def solicitar_prediccion(self, datos_lectura: dict) -> dict:
        """
        Envía datos de lectura al microservicio de IA y recibe la predicción.
        datos_lectura debe contener los campos del schema PredictionRequest:
        heart_rate, spo2, systolic_bp, diastolic_bp, cholesterol, glucose,
        age, sex, chest_pain_type, smoker, previous_condition
        """
        try:
            response = await self.client.post("/predecir", json=datos_lectura)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"error": "timeout", "status": "timeout_microservicio"}
        except httpx.HTTPStatusError as e:
            return {"error": "http_error", "status_code": e.response.status_code}
        except Exception:
            return {"error": "connection_error", "status": "microservicio_no_disponible"}

    async def solicitar_prediccion_typed(self, datos_lectura: dict) -> PrediccionResponse | dict:
        """
        Igual que solicitar_prediccion pero valida y tipa la respuesta
        exitosa como PrediccionResponse. En caso de error retorna el
        dict con la llave 'error'.
        """
        raw = await self.solicitar_prediccion(datos_lectura)
        if "error" in raw:
            return raw
        return PrediccionResponse(**raw)

    def adaptar_a_triaje(self, resp: PrediccionResponse, paciente_id: int,
                         medico_id: int | None = None) -> TriajeCreate:
        """
        Adapta una respuesta exitosa del microservicio al schema TriajeCreate
        que el backend usa para persistencia.
        """
        return TriajeCreate(
            probabilidadRiesgo=resp.risk_score,
            nivelUrgencia=resp.risk_level,
            factoresCriticos=json.dumps(resp.dominant_factors, ensure_ascii=False),
            explicacionClinica=resp.clinical_explanation,
            paciente_id=paciente_id,
            medico_id=medico_id,
        )

    def adaptar_a_alerta(self, resp: PrediccionResponse, paciente_id: int,
                         triaje_id: int | None = None) -> AlertaCreate | None:
        """
        Si threshold_exceeded es True, genera un AlertaCreate.
        Caso contrario retorna None.
        """
        if not resp.threshold_exceeded:
            return None
        return AlertaCreate(
            tipo=resp.risk_level,
            mensaje=resp.recommended_action,
            paciente_id=paciente_id,
            triaje_id=triaje_id,
        )

    async def close(self):
        await self.client.aclose()


# Singleton para reutilizar
microservice_client = MicroserviceClient()
