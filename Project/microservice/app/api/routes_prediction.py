from logging import getLogger

from fastapi import APIRouter, Depends

from app.schemas.explanation import ExplainRequest, ExplainResponse
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services import Services
from app.core.dependencies import get_services

logger = getLogger(__name__)
router = APIRouter()


def _build_rag_info(rag_used: bool, sources: list | None = None):
    if sources:
        return {
            "used": rag_used,
            "sources": [
                {
                    "title": s.get("metadata", {}).get("source", "unknown"),
                    "chunk_id": s.get("metadata", {}).get("chunk_id", ""),
                    "score": s.get("score", 0),
                }
                for s in sources[:3]
            ],
        }
    return {"used": rag_used, "sources": []}


@router.post("/predecir", response_model=PredictionResponse)
async def predecir(req: PredictionRequest, services: Services = Depends(get_services)):
    data = req.model_dump(exclude={"paciente_id", "evento_id", "explain"})
    prediction = services.risk_engine.predict(data)

    rag_sources = None
    clinical_explanation = None

    if req.explain:
        dominant_text = ", ".join(prediction["dominant_factors"])
        rag_sources = services.rag.retrieve(dominant_text)
        rag_info = _build_rag_info(bool(rag_sources), rag_sources)

        clinical_context = {
            "risk_score": prediction["risk_score"],
            "risk_level": prediction["risk_level"],
            "dominant_factors": prediction["dominant_factors"],
        }
        agent_result = await services.agent.explain(
            question=f"Explica el riesgo {prediction['risk_level']} para el paciente",
            context=clinical_context,
        )
        clinical_explanation = agent_result.get("answer", prediction.get("recommended_action", ""))
    else:
        rag_info = {"used": False, "sources": []}

    return PredictionResponse(
        paciente_id=req.paciente_id,
        evento_id=req.evento_id,
        risk_score=prediction["risk_score"],
        risk_level=prediction["risk_level"],
        threshold_exceeded=prediction["threshold_exceeded"],
        dominant_factors=prediction["dominant_factors"],
        clinical_explanation=clinical_explanation,
        recommended_action=prediction["recommended_action"],
        rag=rag_info,
        model={
            "technique": "PSO-optimized weighted risk model",
            "weights_version": services.risk_engine.version,
            "inference_time_ms": 0,
        },
    )


@router.post("/explicar", response_model=ExplainResponse)
async def explicar(req: ExplainRequest, services: Services = Depends(get_services)):
    result = await services.agent.explain(req.question, req.prediction_context)
    sources_data = result.get("sources", result.get("evidence", []))
    return ExplainResponse(
        answer=result.get("answer", "No se pudo generar explicación."),
        sources=sources_data,
    )
