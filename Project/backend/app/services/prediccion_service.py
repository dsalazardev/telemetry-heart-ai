from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.prediccion import PrediccionResponse
from app.schemas.triaje import TriajeCreate
from app.schemas.alerta import AlertaCreate
from app.services.microservice_client import microservice_client
from app.services import triaje_service
from app.services import alerta_service


async def procesar_prediccion(
    db: AsyncSession,
    datos_lectura: dict,
    paciente_id: int,
    medico_id: int | None = None,
) -> dict:
    """
    Flujo completo:
    1. Solicita predicción al microservicio
    2. Adapta la respuesta a TriajeCreate (y opcional AlertaCreate)
    3. Persiste el triaje (y alerta si threshold_exceeded)
    4. Retorna resultado structurado
    """
    raw = await microservice_client.solicitar_prediccion(datos_lectura)

    if "error" in raw:
        return {
            "status": "error",
            "error_type": raw.get("error"),
            "detail": raw.get("status", raw.get("status_code", "desconocido")),
        }

    resp = PrediccionResponse(**raw)

    triaje_data = microservice_client.adaptar_a_triaje(resp, paciente_id, medico_id)
    triaje = await triaje_service.crear_triaje(db, triaje_data)

    alerta = None
    alerta_data = microservice_client.adaptar_a_alerta(resp, paciente_id, triaje.id)
    if alerta_data is not None:
        alerta_data.triaje_id = triaje.id
        alerta = await alerta_service.crear_alerta(
            db,
            tipo=alerta_data.tipo,
            mensaje=alerta_data.mensaje,
            paciente_id=alerta_data.paciente_id,
            medico_id=alerta_data.medico_id,
            triaje_id=alerta_data.triaje_id,
        )

    return {
        "status": "ok",
        "triaje": triaje,
        "alerta": alerta,
        "risk_score": resp.risk_score,
        "risk_level": resp.risk_level,
        "threshold_exceeded": resp.threshold_exceeded,
    }
