import json
from datetime import datetime, timezone
from logging import getLogger
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain.agents.structured_output import ToolStrategy
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.schemas.explanation import ClinicalExplanation
from app.tools.clinical_tools import _make_tools

logger = getLogger(__name__)

SISTEMA_CLINICO = """
Eres un agente clínico de apoyo al triaje cardiovascular.
Tu función es explicar decisiones de priorización generadas por el motor de riesgo.
No diagnosticas, no reemplazas al médico y no inventas evidencia.
Debes usar las tools disponibles cuando necesites cálculo de riesgo o contexto documental.
Responde siempre en JSON estructurado con:
risk_level, explanation, dominant_factors, evidence, recommended_action, limitations.
"""


class AgentService:
    def __init__(self, llm: BaseChatModel, risk_engine, rag):
        self.audit_trail: list[dict] = []
        self.rag = rag
        self.risk_engine = risk_engine
        self.agent = self._build_agent(llm, risk_engine, rag)

    def _build_agent(self, llm: BaseChatModel, risk_engine, rag):
        tools = _make_tools(risk_engine, rag)

        @wrap_tool_call
        def audit_middleware(request, handler):
            step = {
                "tool": str(getattr(request, "name", "unknown")),
                "args": str(getattr(request, "args", {})),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            logger.info("Tool call: %s", step["tool"])
            result = handler(request)
            step["result_summary"] = str(result)[:200]
            self.audit_trail.append(step)
            return result

        return create_agent(
            llm,
            tools,
            system_prompt=SISTEMA_CLINICO,
            response_format=ToolStrategy(ClinicalExplanation),
            middleware=[audit_middleware],
        )

    async def explain(self, question: str, context: dict | None = None) -> dict[str, Any]:
        self.audit_trail = []
        context_str = json.dumps(context, ensure_ascii=False) if context else "sin contexto adicional"
        user_msg = f"Pregunta: {question}\nContexto de predicción: {context_str}"

        try:
            result = await self.agent.ainvoke({
                "messages": [
                    SystemMessage(content=SISTEMA_CLINICO),
                    HumanMessage(content=user_msg),
                ]
            })
            structured = result.get("structured_response")
            if structured and isinstance(structured, ClinicalExplanation):
                return {
                    "answer": structured.explanation,
                    "risk_level": structured.risk_level,
                    "risk_score": structured.risk_score,
                    "dominant_factors": structured.dominant_factors,
                    "evidence": [e.model_dump() for e in structured.evidence],
                    "recommended_action": structured.recommended_action,
                    "limitations": structured.limitations,
                    "sources": [e.model_dump() for e in structured.evidence],
                    "audit_trail": self.audit_trail,
                }
            return {
                "answer": "No se pudo generar una explicación estructurada.",
                "sources": [],
            }
        except Exception as e:
            logger.error("Error en agente LangChain: %s", e)
            return {
                "answer": f"Error generando explicación: {str(e)}. La predicción numérica está disponible en /predecir.",
                "sources": [],
                "error": str(e),
            }
