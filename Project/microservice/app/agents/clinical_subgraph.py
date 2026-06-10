import json
from logging import getLogger
from datetime import datetime, timezone

from langgraph.graph import StateGraph, START, END
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from fastapi import APIRouter, Depends

from app.core.langgraph_state import ClinicalState
from app.core.langsmith import trace_node
from app.core.dependencies import get_services
from app.schemas.explanation import ExplainRequest, ExplainResponse
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.risk_engine import RiskEngine
from app.services.rag_service import RagService
from fastapi import APIRouter, Depends
from app.agents.base import BaseAgent

logger = getLogger(__name__)

SISTEMA_CLINICO = """
Eres un agente clínico de apoyo al triaje cardiovascular.
Tu función es explicar decisiones de priorización generadas por el motor de riesgo.
No diagnosticas, no reemplazas al médico y no inventas evidencia.
Responde en JSON con:
- risk_level: "bajo" | "medio" | "alto"
- risk_score: float
- dominant_factors: list[str]
- explanation: string
- evidence: list[{"title", "chunk_id", "score"}]
- recommended_action: string
- limitations: string
"""


def _build_rag_info(rag_sources: list | None, max_sources: int = 4):
    if not rag_sources:
        return {"used": False, "sources": []}
    return {
        "used": True,
        "sources": [
            {
                "title": s.get("metadata", {}).get("source", "unknown"),
                "chunk_id": s.get("metadata", {}).get("chunk_id", ""),
                "score": s.get("score", 0),
            }
            for s in rag_sources[:max_sources]
        ],
    }


class ClinicalGraph(BaseAgent):
    name = "clinical"
    def __init__(self, llm: BaseChatModel, risk_engine: RiskEngine, rag: RagService):
        self.llm = llm
        self.risk_engine = risk_engine
        self.rag = rag
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        builder = StateGraph(ClinicalState)

        builder.add_node("normalize_and_predict", self._normalize_and_predict)
        builder.add_node("retrieve_rag", self._retrieve_rag)
        builder.add_node("explain", self._explain)
        builder.add_node("format_response", self._format_response)

        builder.add_edge(START, "normalize_and_predict")
        builder.add_conditional_edges(
            "normalize_and_predict",
            self._should_explain,
            {True: "retrieve_rag", False: "format_response"},
        )
        builder.add_edge("retrieve_rag", "explain")
        builder.add_edge("explain", "format_response")
        builder.add_edge("format_response", END)

        return builder.compile()

    def _should_explain(self, state: ClinicalState) -> bool:
        return bool(state["request"] and state["request"].explain)

    @trace_node("normalize_and_predict")
    async def _normalize_and_predict(self, state: ClinicalState) -> dict:
        req = state["request"]
        if req is None:
            return {"error": "request is None"}
        data = req.model_dump(exclude={"paciente_id", "evento_id", "explain"})
        risk = self.risk_engine.predict(data)
        return {"features": data, "risk_result": risk}

    @trace_node("retrieve_rag")
    async def _retrieve_rag(self, state: ClinicalState) -> dict:
        dominant = state["risk_result"].get("dominant_factors", [])
        query = ", ".join(dominant) if dominant else "factores de riesgo cardiovascular"
        k = getattr(self.rag, "retrieval_k", 4)
        sources = await self.rag.retrieve_async(query, k=k)
        return {"rag_sources": sources}

    @trace_node("explain")
    async def _explain(self, state: ClinicalState) -> dict:
        risk = state["risk_result"]
        k = getattr(self.rag, "retrieval_k", 4)
        rag_info = _build_rag_info(state["rag_sources"], max_sources=k)
        context = {
            "risk_score": risk.get("risk_score"),
            "risk_level": risk.get("risk_level"),
            "dominant_factors": risk.get("dominant_factors"),
            "rag_sources": rag_info["sources"],
        }
        user_msg = (
            f"Contexto de predicción: {json.dumps(context, ensure_ascii=False)}\n"
            f"Explica el riesgo {risk.get('risk_level')} para el paciente"
        )
        try:
            messages = [
                SystemMessage(content=SISTEMA_CLINICO),
                HumanMessage(content=user_msg),
            ]
            response = await self.llm.ainvoke(messages)
            output = response.content if hasattr(response, "content") else str(response)
            try:
                parsed = json.loads(output)
                explanation = parsed.get("explanation", output)
            except (json.JSONDecodeError, KeyError):
                explanation = output
        except Exception as e:
            logger.error("Error en LLM explain: %s", e)
            explanation = risk.get("recommended_action", "No se pudo generar explicación.")

        return {"clinical_explanation": explanation}

    @trace_node("format_response")
    async def _format_response(self, state: ClinicalState) -> dict:
        req = state["request"]
        risk = state["risk_result"]
        rag_info = _build_rag_info(state["rag_sources"]) if state["rag_sources"] else {"used": False, "sources": []}

        response = PredictionResponse(
            paciente_id=req.paciente_id if req else None,
            evento_id=req.evento_id if req else None,
            risk_score=risk.get("risk_score", 0.0),
            risk_level=risk.get("risk_level", "bajo"),
            threshold_exceeded=risk.get("threshold_exceeded", False),
            dominant_factors=risk.get("dominant_factors", []),
            clinical_explanation=state.get("clinical_explanation"),
            recommended_action=risk.get("recommended_action", ""),
            rag=rag_info,
            model={
                "technique": "PSO-optimized weighted risk model",
                "weights_version": getattr(self.risk_engine, "version", "unknown"),
                "inference_time_ms": 0,
            },
        )
        return {"response": response}

    async def run(self, request: PredictionRequest | None = None, **kwargs) -> PredictionResponse:
        if request is None:
            raise ValueError("ClinicalGraph.run() requiere 'request'")
        initial = ClinicalState(
            request=request,
            features={},
            risk_result={},
            rag_sources=None,
            clinical_explanation=None,
            response=None,
            error=None,
        )
        result = await self.graph.ainvoke(initial)
        if result.get("error"):
            raise RuntimeError(result["error"])
        return result["response"]

    @property
    def router(self) -> APIRouter:
        router = APIRouter(tags=["prediction"])

        @router.post("/predecir", response_model=PredictionResponse)
        async def predecir(req: PredictionRequest, services=Depends(get_services)):
            clinical = services.agents.get("clinical")
            if clinical is None:
                return PredictionResponse(
                    risk_score=0.0, risk_level="bajo", threshold_exceeded=False,
                    dominant_factors=["error"], recommended_action="clinical agent no disponible",
                    rag={"used": False, "sources": []},
                    model={"technique": "error", "weights_version": "unknown", "inference_time_ms": 0},
                )
            try:
                return await clinical.run(request=req)
            except Exception as e:
                logger.error("Error en /predecir: %s", e)
                return PredictionResponse(
                    paciente_id=req.paciente_id, evento_id=req.evento_id,
                    risk_score=0.0, risk_level="bajo", threshold_exceeded=False,
                    dominant_factors=["error en procesamiento"],
                    clinical_explanation=str(e),
                    recommended_action="Error en microservicio. Reintentar más tarde.",
                    rag={"used": False, "sources": []},
                    model={"technique": "error", "weights_version": "unknown", "inference_time_ms": 0},
                )

        @router.post("/explicar", response_model=ExplainResponse)
        async def explicar(req: ExplainRequest, services=Depends(get_services)):
            llm = getattr(getattr(services, "clinical_graph", None), "llm", None)
            if llm is None:
                return ExplainResponse(answer="LLM no disponible", sources=[])
            context_str = str(req.prediction_context) if req.prediction_context else "sin contexto"
            messages = [
                SystemMessage(content="Eres un agente clínico. Responde la pregunta del médico basándote en el contexto proporcionado."),
                HumanMessage(content=f"Contexto: {context_str}\n\nPregunta: {req.question}"),
            ]
            try:
                response = await llm.ainvoke(messages)
                answer = response.content if hasattr(response, "content") else str(response)
            except Exception as e:
                logger.error("Error en /explicar: %s", e)
                answer = "No se pudo generar explicación."
            return ExplainResponse(answer=answer, sources=[])

        return router
