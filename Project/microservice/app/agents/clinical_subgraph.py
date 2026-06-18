import json
import re
from logging import getLogger
from datetime import datetime, timezone

from langgraph.graph import StateGraph, START, END
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from fastapi import APIRouter, Depends
from pydantic import ValidationError

from app.core.langgraph_state import ClinicalState
from app.core.dependencies import get_services, verify_internal_token
from app.schemas.explanation import ClinicalExplanation, ExplainRequest, ExplainResponse
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.risk_engine import RiskEngine
from app.services.rag_service import RAGService
from app.services.triage_priority_service import (
    TriagePriorityService,
    build_feature_bundle,
    FeatureBundle,
)
from app.tools import ALL_TOOLS
from app.agents.base import BaseAgent

logger = getLogger(__name__)

PROMPT_VERSION = "clinical_prompt_v3"
# Umbral de similitud coseno para aceptar evidencia RAG. MiniLM sobre texto
# clínico en español rinde scores ~0.5-0.7 en matches relevantes; 0.65 era
# demasiado estricto y descartaba evidencia válida ("evidencia insuficiente").
MIN_RAG_SCORE = 0.5

# Mapeo string→numérico de chest_pain. Debe coincidir con
# `generate_synthetic.CHEST_PAIN_MAP` y `RiskEngine._chest_map`: el PSO se
# entrena con el valor numérico 1-4, así que el runtime debe convertir el
# `chest_pain_type` del request al mismo espacio antes de priorizar.
CHEST_PAIN_MAP = {
    "typical_angina": 1.0,
    "atypical_angina": 2.0,
    "non_anginal": 3.0,
    "asymptomatic": 4.0,
}

CLINICAL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
Eres un agente clínico de apoyo al triaje cardiovascular.
No diagnosticas, no reemplazas al médico y no inventas evidencia.
Responde únicamente en JSON válido con las claves exactas solicitadas.
"""),
    ("human", """
Riesgo calculado:
- score: {risk_score}
- nivel (3-niveles baseline): {risk_level}
- prioridad (3-niveles PSO): {priority_label} (score={priority_score})

Factores dominantes: {dominant_factors}

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


def _strip_json_fence(text: str) -> str:
    """Quita el envoltorio markdown ```json ... ``` que añaden algunos LLMs
    (p. ej. gpt-4o-mini), para que ``model_validate_json`` pueda parsear."""
    t = (text or "").strip()
    m = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```$", t, re.DOTALL)
    return m.group(1).strip() if m else t


def build_safe_fallback_explanation(risk_result: dict, rag_sources: list | None) -> ClinicalExplanation:
    sources = []
    if rag_sources:
        for s in rag_sources[:4]:
            sources.append({
                "title": s.get("metadata", {}).get("source", "unknown"),
                "chunk_id": s.get("metadata", {}).get("chunk_id", ""),
                "score": s.get("score", 0),
            })
    level = risk_result.get("risk_level", "bajo")
    score = risk_result.get("risk_score", 0.0)
    factors = risk_result.get("dominant_factors", []) or []
    factors_txt = ", ".join(factors) if factors else "sin factores dominantes significativos"
    n_src = len(sources)
    # Explicación compuesta a partir de los datos reales del caso (no el texto
    # de la recomendación). Determinista, sin LLM, pero específica por paciente.
    explanation = (
        f"El RiskEngine estima un riesgo {level} (score {score:.2f}) a partir de "
        f"los signos clínicos. Factores con mayor peso: {factors_txt}."
    )
    if n_src:
        explanation += f" Coherente con {n_src} fuente(s) de la guía clínica indexada."
    return ClinicalExplanation(
        risk_level=level,
        risk_score=score,
        dominant_factors=factors,
        explanation=explanation,
        evidence=sources,
        recommended_action=risk_result.get("recommended_action", ""),
        limitations="Explicación generada por reglas (RiskEngine), sin redacción del LLM.",
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


def _coerce_request(req) -> PredictionRequest:
    """Normaliza ``state['request']`` a ``PredictionRequest``.

    LangGraph Studio envía el state como JSON, por lo que ``request`` llega
    como ``dict`` puro. Los tests en Python y el método ``run()`` lo
    entregan ya como ``PredictionRequest``. Este helper acepta ambos y
    devuelve siempre el modelo Pydantic.
    """
    if isinstance(req, PredictionRequest):
        return req
    if isinstance(req, dict):
        return PredictionRequest.model_validate(req)
    raise TypeError(
        f"state['request'] debe ser dict o PredictionRequest, "
        f"recibió {type(req).__name__}"
    )


class ClinicalGraph(BaseAgent):
    name = "clinical"

    def __init__(
        self,
        llm: BaseChatModel,
        risk_engine: RiskEngine,
        rag: RAGService,
        triage_priority: TriagePriorityService,
    ):
        self.llm = llm
        self.risk_engine = risk_engine
        self.rag = rag
        self.triage_priority = triage_priority
        # Toolset LangChain registrado para el agente. No se hace `bind_tools`
        # al LLM: el `optimize_triage_priority_tool` corre offline (Studio /
        # scripts de evaluación), no dentro del flujo de `/predecir`.
        self.tools = list(ALL_TOOLS)
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        builder = StateGraph(ClinicalState)

        builder.add_node("normalize_and_predict", self._normalize_and_predict)
        builder.add_node("prioritize", self._prioritize)
        builder.add_node("retrieve_rag", self._retrieve_rag)
        builder.add_node("explain", self._explain)
        builder.add_node("format_response", self._format_response)

        builder.add_edge(START, "normalize_and_predict")
        builder.add_edge("normalize_and_predict", "prioritize")
        builder.add_conditional_edges(
            "prioritize",
            self._should_explain,
            {True: "retrieve_rag", False: "format_response"},
        )
        builder.add_edge("retrieve_rag", "explain")
        builder.add_edge("explain", "format_response")
        builder.add_edge("format_response", END)

        return builder.compile()

    def _should_explain(self, state: ClinicalState) -> bool:
        if not state["request"]:
            return False
        try:
            req = _coerce_request(state["request"])
        except (TypeError, ValidationError):
            return False
        return bool(req.explain)

    async def _normalize_and_predict(self, state: ClinicalState) -> dict:
        req_raw = state["request"]
        if req_raw is None:
            return {"error": "request is None"}
        try:
            req = _coerce_request(req_raw)
        except (TypeError, ValidationError) as e:
            return {"error": f"invalid request payload: {e}"}
        data = req.model_dump(exclude={"paciente_id", "evento_id", "explain"})
        risk = self.risk_engine.predict(data)
        return {"features": data, "risk_result": risk}

    async def _prioritize(self, state: ClinicalState) -> dict:
        data = state["features"]
        # El request expone `chest_pain_type` (string); el PSO espera el
        # numérico 1-4. Sin esta conversión la feature llega siempre como 0.
        chest_pain = CHEST_PAIN_MAP.get(data.get("chest_pain_type"))
        bundle = build_feature_bundle(
            heart_rate=data.get("heart_rate"),
            spo2=data.get("spo2"),
            systolic_bp=data.get("systolic_bp"),
            cholesterol=data.get("cholesterol"),
            chest_pain=chest_pain,
            age=data.get("age"),
            smoker=data.get("smoker"),
            previous_condition=data.get("previous_condition"),
        )
        priority = self.triage_priority.classify(bundle)
        return {"priority_result": priority}

    async def _retrieve_rag(self, state: ClinicalState) -> dict:
        dominant = state["risk_result"].get("dominant_factors", [])
        query = ", ".join(dominant) if dominant else "factores de riesgo cardiovascular"
        k = getattr(self.rag, "retrieval_k", 4)
        sources = await self.rag.retrieve_async(query, k=k)
        return {"rag_sources": sources}

    async def _explain(self, state: ClinicalState) -> dict:
        risk = state["risk_result"]
        priority = state.get("priority_result")
        k = getattr(self.rag, "retrieval_k", 4)

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
            chain = CLINICAL_PROMPT | self.llm
            response = await chain.ainvoke({
                "risk_score": risk.get("risk_score", 0.0),
                "risk_level": risk.get("risk_level", "bajo"),
                "priority_label": priority.priority_label if priority else "N/D",
                "priority_score": priority.score if priority else 0.0,
                "dominant_factors": ", ".join(risk.get("dominant_factors", [])),
                "rag_sources": json.dumps(rag_info["sources"], ensure_ascii=False),
            })
            output = response.content if hasattr(response, "content") else str(response)
            output = _strip_json_fence(output)
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
        req = _coerce_request(state["request"]) if state["request"] else None
        risk = state["risk_result"]
        priority = state.get("priority_result")
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
                "technique": "RiskEngine (sigmoid 11-pesos) + TriagePriorityService (PSO)",
                "weights_version": getattr(self.risk_engine, "version", "unknown"),
                "prompt_version": PROMPT_VERSION,
                "rag_collection_version": "guidelines_v1",
                "inference_time_ms": 0,
            },
            priority=priority.priority_label if priority else None,
            priority_score=priority.score if priority else None,
            priority_level=priority.priority_level if priority else None,
            weights_version=priority.weights_version if priority else None,
        )
        return {"response": response}

    async def run(self, request: PredictionRequest | None = None, **kwargs) -> PredictionResponse:
        if request is None:
            raise ValueError("ClinicalGraph.run() requiere 'request'")
        initial = ClinicalState(
            request=request,
            features={},
            risk_result={},
            priority_result=None,
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

        @router.post("/predecir", response_model=PredictionResponse, dependencies=[Depends(verify_internal_token)])
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
                logger.error(
                    "Error en /predecir (paciente_id=%s, %s): %s",
                    req.paciente_id, type(e).__name__, e, exc_info=True,
                )
                return PredictionResponse(
                    paciente_id=req.paciente_id, evento_id=req.evento_id,
                    risk_score=0.0, risk_level="bajo", threshold_exceeded=False,
                    dominant_factors=["error en procesamiento"],
                    clinical_explanation=str(e),
                    recommended_action="Error en microservicio. Reintentar más tarde.",
                    rag={"used": False, "sources": []},
                    model={"technique": "error", "weights_version": "unknown", "prompt_version": PROMPT_VERSION, "inference_time_ms": 0},
                )

        @router.post("/explicar", response_model=ExplainResponse, dependencies=[Depends(verify_internal_token)])
        async def explicar(req: ExplainRequest, services=Depends(get_services)):
            llm = getattr(getattr(services, "clinical_graph", None), "llm", None)
            if llm is None:
                return ExplainResponse(answer="LLM no disponible", sources=[])
            context_str = str(req.prediction_context) if req.prediction_context else "sin contexto"
            try:
                chain = MEDICO_EXPLAIN_PROMPT | llm
                response = await chain.ainvoke({
                    "context": context_str,
                    "question": req.question,
                })
                answer = response.content if hasattr(response, "content") else str(response)
            except Exception as e:
                logger.error("Error en /explicar: %s", e)
                answer = "No se pudo generar explicación."
            return ExplainResponse(answer=answer, sources=[])

        return router
