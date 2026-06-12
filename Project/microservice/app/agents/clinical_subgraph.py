import json
from logging import getLogger
from datetime import datetime, timezone

from langgraph.graph import StateGraph, START, END
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from fastapi import APIRouter, Depends

from app.core.langgraph_state import ClinicalState
from app.core.dependencies import get_services
from app.schemas.explanation import ClinicalExplanation, ExplainRequest, ExplainResponse
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.risk_engine import RiskEngine
from app.services.rag_service import RAGService
from fastapi import APIRouter, Depends
from app.agents.base import BaseAgent
from pydantic import ValidationError

logger = getLogger(__name__)

PROMPT_VERSION = "clinical_prompt_v2"
MIN_RAG_SCORE = 0.65

CLINICAL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
Eres un agente clínico de apoyo al triaje cardiovascular.
No diagnosticas, no reemplazas al médico y no inventas evidencia.
Responde únicamente en JSON válido con las claves exactas solicitadas.
"""),
    ("human", """
Riesgo calculado:
- score: {risk_score}
- nivel: {risk_level}
- factores dominantes: {dominant_factors}

Evidencia RAG:
{rag_sources}

Genera obligatoriamente:
risk_level, risk_score, dominant_factors, explanation, evidence,
recommended_action, limitations.
"""),
])

MEDICO_EXPLAIN_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Eres un agente clínico. Responde la pregunta del médico basándote en el contexto proporcionado."),
    ("human", "Contexto: {context}\n\nPregunta: {question}"),
])


def build_safe_fallback_explanation(risk_result: dict, rag_sources: list | None) -> ClinicalExplanation:
    sources = []
    if rag_sources:
        for s in rag_sources[:4]:
            sources.append({
                "title": s.get("metadata", {}).get("source", "unknown"),
                "chunk_id": s.get("metadata", {}).get("chunk_id", ""),
                "score": s.get("score", 0),
            })
    return ClinicalExplanation(
        risk_level=risk_result.get("risk_level", "bajo"),
        risk_score=risk_result.get("risk_score", 0.0),
        dominant_factors=risk_result.get("dominant_factors", []),
        explanation=risk_result.get("recommended_action", "No se pudo generar explicación con LLM."),
        evidence=sources,
        recommended_action=risk_result.get("recommended_action", ""),
        limitations="La explicación se limita al cálculo del RiskEngine sin validación de LLM.",
    )


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
    def __init__(self, llm: BaseChatModel, risk_engine: RiskEngine, rag: RAGService):
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

    async def _normalize_and_predict(self, state: ClinicalState) -> dict:
        req = state["request"]
        if req is None:
            return {"error": "request is None"}
        data = req.model_dump(exclude={"paciente_id", "evento_id", "explain"})
        risk = self.risk_engine.predict(data)
        return {"features": data, "risk_result": risk}

    async def _retrieve_rag(self, state: ClinicalState) -> dict:
        dominant = state["risk_result"].get("dominant_factors", [])
        query = ", ".join(dominant) if dominant else "factores de riesgo cardiovascular"
        k = getattr(self.rag, "retrieval_k", 4)
        sources = await self.rag.retrieve_async(query, k=k)
        return {"rag_sources": sources}

    async def _explain(self, state: ClinicalState) -> dict:
        risk = state["risk_result"]
        k = getattr(self.rag, "retrieval_k", 4)

        # Filtro de evidencia por score mínimo
        raw_sources = state.get("rag_sources") or []
        valid_sources = [s for s in raw_sources if s.get("score", 0) >= MIN_RAG_SCORE]

        if not valid_sources:
            logger.warning("No se encontró evidencia RAG con score >= %s", MIN_RAG_SCORE)
            return {
                "clinical_explanation": (
                    "No se encontró evidencia suficiente en la base documental indexada. "
                    "La explicación se limita al cálculo del RiskEngine."
                ),
                "clinical_explanation_structured": build_safe_fallback_explanation(
                    risk, valid_sources
                ).model_dump(),
            }

        rag_info = _build_rag_info(valid_sources, max_sources=k)

        try:
            messages = CLINICAL_PROMPT.format_messages(
                risk_score=risk.get("risk_score", 0.0),
                risk_level=risk.get("risk_level", "bajo"),
                dominant_factors=", ".join(risk.get("dominant_factors", [])),
                rag_sources=json.dumps(rag_info["sources"], ensure_ascii=False),
            )
            response = await self.llm.ainvoke(messages)
            output = response.content if hasattr(response, "content") else str(response)
            try:
                parsed = ClinicalExplanation.model_validate_json(output)
                return {
                    "clinical_explanation": parsed.explanation,
                    "clinical_explanation_structured": parsed.model_dump(),
                }
            except (ValidationError, json.JSONDecodeError) as e:
                logger.warning("LLM output no validó contra ClinicalExplanation: %s", e)
                fallback = build_safe_fallback_explanation(risk, valid_sources)
                return {
                    "clinical_explanation": fallback.explanation,
                    "clinical_explanation_structured": fallback.model_dump(),
                }
        except Exception as e:
            logger.error("Error en LLM explain: %s", e)
            fallback = build_safe_fallback_explanation(risk, valid_sources)
            return {
                "clinical_explanation": fallback.explanation,
                "clinical_explanation_structured": fallback.model_dump(),
            }

    async def _format_response(self, state: ClinicalState) -> dict:
        req = state["request"]
        risk = state["risk_result"]
        rag_info = _build_rag_info(state["rag_sources"]) if state["rag_sources"] else {"used": False, "sources": []}

        structured = state.get("clinical_explanation_structured")
        if structured:
            try:
                explanation_structured = ClinicalExplanation.model_validate(structured)
            except ValidationError:
                explanation_structured = None
        else:
            explanation_structured = None

        response = PredictionResponse(
            paciente_id=req.paciente_id if req else None,
            evento_id=req.evento_id if req else None,
            risk_score=risk.get("risk_score", 0.0),
            risk_level=risk.get("risk_level", "bajo"),
            threshold_exceeded=risk.get("threshold_exceeded", False),
            dominant_factors=risk.get("dominant_factors", []),
            clinical_explanation=state.get("clinical_explanation"),
            explanation_structured=explanation_structured,
            recommended_action=risk.get("recommended_action", ""),
            rag=rag_info,
            model={
                "technique": "PSO-optimized weighted risk model",
                "weights_version": getattr(self.risk_engine, "version", "unknown"),
                "prompt_version": PROMPT_VERSION,
                "rag_collection_version": "guidelines_v1",
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
                    model={"technique": "error", "weights_version": "unknown", "prompt_version": PROMPT_VERSION, "inference_time_ms": 0},
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
                    model={"technique": "error", "weights_version": "unknown", "prompt_version": PROMPT_VERSION, "inference_time_ms": 0},
                )

        @router.post("/explicar", response_model=ExplainResponse)
        async def explicar(req: ExplainRequest, services=Depends(get_services)):
            llm = getattr(getattr(services, "clinical_graph", None), "llm", None)
            if llm is None:
                return ExplainResponse(answer="LLM no disponible", sources=[])
            context_str = str(req.prediction_context) if req.prediction_context else "sin contexto"
            messages = MEDICO_EXPLAIN_PROMPT.format_messages(
                context=context_str,
                question=req.question,
            )
            try:
                response = await llm.ainvoke(messages)
                answer = response.content if hasattr(response, "content") else str(response)
            except Exception as e:
                logger.error("Error en /explicar: %s", e)
                answer = "No se pudo generar explicación."
            return ExplainResponse(answer=answer, sources=[])

        return router
