from logging import getLogger
from pathlib import Path

import yaml
from langgraph.graph import StateGraph, START, END
from fastapi import APIRouter, Depends, HTTPException

from app.core.langgraph_state import N8NState
from app.core.langsmith import trace_node
from app.core.dependencies import get_services
from app.services.risk_engine import RiskEngine
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.agents.base import BaseAgent

logger = getLogger(__name__)

# Simple in-memory deduplication cache for webhook events
_EVENT_CACHE: dict[str, dict] = {}
_MAX_CACHE_SIZE = 1000


def _get_cached_event(event_id: str) -> dict | None:
    return _EVENT_CACHE.get(event_id)


def _cache_event(event_id: str, response: dict) -> None:
    if len(_EVENT_CACHE) >= _MAX_CACHE_SIZE:
        keys = list(_EVENT_CACHE.keys())
        for k in keys[:_MAX_CACHE_SIZE // 2]:
            del _EVENT_CACHE[k]
    _EVENT_CACHE[event_id] = response


_DEFAULT_N8N_CFG = Path(__file__).parent.parent / "config" / "clinical_params.yaml"


def _load_n8n_config(path: str | Path | None = None) -> dict:
    p = Path(path) if path else _DEFAULT_N8N_CFG
    if p.exists():
        with open(p) as f:
            cfg = yaml.safe_load(f)
            return cfg.get("n8n_thresholds", {})
    return {}


_N8N_THRESHOLDS = _load_n8n_config()


def _num(value, fallback=None):
    if value is None or value == "":
        return fallback
    try:
        v = float(value)
        return v
    except (ValueError, TypeError):
        return fallback


def _bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "si", "sí", "yes")
    return bool(value)


def _check_thresholds(parsed: dict, thresholds: dict | None = None) -> list[str]:
    t = thresholds or _N8N_THRESHOLDS
    flags = []
    hr = _num(parsed.get("heart_rate"))
    spo2 = _num(parsed.get("spo2"))
    sbp = _num(parsed.get("systolic_bp"))
    dbp = _num(parsed.get("diastolic_bp"))
    chol = _num(parsed.get("cholesterol"))
    gluc = _num(parsed.get("glucose"))

    if hr is not None and hr >= t.get("tachycardia", 130):
        flags.append("taquicardia >= 130 bpm")
    if hr is not None and hr > 0 and hr <= t.get("bradycardia", 45):
        flags.append("bradicardia <= 45 bpm")
    if spo2 is not None and spo2 <= t.get("spo2_critical", 92):
        flags.append("SpO2 <= 92%")
    if sbp is not None and sbp >= t.get("systolic_critical", 160):
        flags.append("presion sistolica >= 160 mmHg")
    if dbp is not None and dbp >= t.get("diastolic_critical", 100):
        flags.append("presion diastolica >= 100 mmHg")
    if chol is not None and chol >= t.get("cholesterol_critical", 240):
        flags.append("colesterol >= 240 mg/dL")
    if gluc is not None and gluc >= t.get("glucose_critical", 180):
        flags.append("glucosa >= 180 mg/dL")

    return flags


class N8NGraph(BaseAgent):
    name = "n8n"
    def __init__(self, risk_engine: RiskEngine, clinical_graph=None, config: dict | None = None):
        self.risk_engine = risk_engine
        self.clinical_graph = clinical_graph
        self.config = config or _load_n8n_config()
        if "n8n_thresholds" in self.config:
            self.config = self.config
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        builder = StateGraph(N8NState)

        builder.add_node("parse_payload", self._parse_payload)
        builder.add_node("check_thresholds", self._check_thresholds)
        builder.add_node("call_clinical", self._call_clinical)
        builder.add_node("build_fallback", self._build_fallback)
        builder.add_node("format_n8n", self._format_n8n)

        builder.add_edge(START, "parse_payload")
        builder.add_edge("parse_payload", "check_thresholds")
        builder.add_conditional_edges(
            "check_thresholds",
            self._needs_prediction,
            {True: "call_clinical", False: "format_n8n"},
        )
        builder.add_conditional_edges(
            "call_clinical",
            self._clinical_ok,
            {True: "format_n8n", False: "build_fallback"},
        )
        builder.add_edge("build_fallback", "format_n8n")
        builder.add_edge("format_n8n", END)

        return builder.compile()

    def _needs_prediction(self, state: N8NState) -> bool:
        return len(state.get("threshold_flags", [])) > 0

    def _clinical_ok(self, state: N8NState) -> bool:
        return state.get("clinical_result") is not None and "error" not in state["clinical_result"]

    @trace_node("parse_payload")
    async def _parse_payload(self, state: N8NState) -> dict:
        body = state["raw_payload"]
        parsed = {
            "paciente_id": body.get("paciente_id") or body.get("pacienteId") or body.get("patient_id"),
            "dispositivo_id": body.get("dispositivo_id") or body.get("dispositivoId") or body.get("device_id"),
            "heart_rate": _num(body.get("heart_rate") or body.get("frecuencia_cardiaca") or body.get("hr")),
            "spo2": _num(body.get("spo2") or body.get("oxigenacion")),
            "systolic_bp": _num(body.get("systolic_bp") or body.get("presion_sistolica") or body.get("sbp")),
            "diastolic_bp": _num(body.get("diastolic_bp") or body.get("presion_diastolica") or body.get("dbp")),
            "cholesterol": _num(body.get("cholesterol") or body.get("colesterol")),
            "glucose": _num(body.get("glucose") or body.get("glucosa")),
            "age": _num(body.get("age") or body.get("edad")),
            "sex": body.get("sex") or body.get("sexo"),
            "smoker": _bool(body.get("smoker") or body.get("fumador")),
            "chest_pain_type": body.get("chest_pain_type") or body.get("dolor_toracico"),
            "previous_condition": _bool(body.get("previous_condition") or body.get("condicion_previa")),
            "event_id": body.get("event_id") or body.get("telemetry_id") or body.get("id"),
        }
        return {"parsed_data": parsed}

    @trace_node("check_thresholds")
    async def _check_thresholds(self, state: N8NState) -> dict:
        t = self.config.get("n8n_thresholds", self.config) if isinstance(self.config, dict) else {}
        flags = _check_thresholds(state["parsed_data"], thresholds=t)
        return {"threshold_flags": flags, "action": "predict" if flags else "passthrough"}

    @trace_node("call_clinical")
    async def _call_clinical(self, state: N8NState) -> dict:
        if self.clinical_graph is None:
            return {"clinical_result": {"error": "clinical_graph no disponible"}}

        p = state["parsed_data"]
        req = PredictionRequest(
            paciente_id=p.get("paciente_id"),
            heart_rate=p.get("heart_rate") or 0,
            spo2=p.get("spo2"),
            systolic_bp=p.get("systolic_bp"),
            diastolic_bp=p.get("diastolic_bp"),
            cholesterol=p.get("cholesterol"),
            glucose=p.get("glucose"),
            age=int(p["age"]) if p.get("age") else None,
            sex=p.get("sex"),
            smoker=p.get("smoker"),
            chest_pain_type=p.get("chest_pain_type"),
            previous_condition=p.get("previous_condition"),
            explain=True,
        )
        try:
            pred: PredictionResponse = await self.clinical_graph.run(req)
            return {"clinical_result": pred.model_dump()}
        except Exception as e:
            return {"clinical_result": {"error": str(e)}}

    @trace_node("build_fallback")
    async def _build_fallback(self, state: N8NState) -> dict:
        fb = self.config.get("fallback", {})
        crit_flags = fb.get("critical_flags", 3)
        high_flags = fb.get("high_flags", 1)
        crit_score = fb.get("critical_score", 0.85)
        high_score = fb.get("high_score", 0.62)
        low_score = fb.get("low_score", 0.25)

        flags = state.get("threshold_flags", [])
        n = len(flags)
        risk_level = "ALTO" if n >= crit_flags else ("MEDIO" if n >= high_flags else "BAJO")
        score = crit_score if n >= crit_flags else (high_score if n >= high_flags else low_score)
        return {
            "clinical_result": {
                "risk_score": score,
                "risk_level": risk_level.lower(),
                "threshold_exceeded": n >= 3,
                "dominant_factors": flags or ["sin umbrales críticos"],
                "clinical_explanation": None,
                "recommended_action": "Monitoreo continuo" if n == 0 else "Generar alerta y solicitar revisión",
                "fuente": "fallback_reglas_n8n",
            }
        }

    @trace_node("format_n8n")
    async def _format_n8n(self, state: N8NState) -> dict:
        pred = state.get("clinical_result") or {}
        flags = state.get("threshold_flags", [])
        parsed = state.get("parsed_data", {})
        pid = parsed.get("paciente_id", "sin_id")
        rl = pred.get("risk_level", "bajo").upper()
        sc = pred.get("risk_score", 0.0)
        prioridad = "CRITICA" if rl == "ALTO" or sc >= 0.75 else ("ALTA" if rl == "MEDIO" else "MEDIA")

        resumen = (
            f"Paciente {pid} con riesgo {rl}. "
            f"Flags: {'; '.join(flags) if flags else 'sin umbrales críticos'}. "
            f"Score: {sc}. "
            f"Fuente: {pred.get('fuente', 'microservice')}."
        )

        n8n_response = {
            "riesgo": rl,
            "score": sc,
            "prioridad": prioridad,
            "flags_umbral": flags,
            "resumen_clinico": resumen,
            "prediccion": pred,
            "microservice_fallo": "error" in pred,
            "alerta": {
                "paciente_id": pid,
                "tipo": "riesgo_cardiovascular",
                "prioridad": prioridad,
                "riesgo": rl,
                "score": sc,
                "mensaje": resumen,
                "flags": flags,
                "origen": "n8n_agent",
            },
        }
        return {"n8n_response": n8n_response}

    async def run(self, payload: dict | None = None, **kwargs) -> dict:
        event_id = payload.get("event_id") if payload else None
        if event_id:
            cached = _get_cached_event(event_id)
            if cached is not None:
                logger.info("Evento %s ya procesado; devolviendo respuesta cacheada", event_id)
                return {"n8n_response": {**cached, "deduplicated": True}}

        initial = N8NState(
            raw_payload=payload,
            parsed_data={},
            action="",
            threshold_flags=[],
            clinical_result=None,
            n8n_response={},
            error=None,
        )
        result = await self.graph.ainvoke(initial)
        n8n_response = result.get("n8n_response", {"error": "no_response"})

        if event_id:
            _cache_event(event_id, n8n_response)

        return {"n8n_response": n8n_response}

    @property
    def router(self) -> APIRouter:
        router = APIRouter(tags=["n8n"])

        async def _handle_payload(payload: dict, services):
            n8n = services.agents.get("n8n")
            if n8n is None:
                raise HTTPException(status_code=500, detail="n8n agent no disponible")
            try:
                return await n8n.run(payload=payload)
            except Exception as e:
                logger.error("Error en n8n agent: %s", e)
                raise HTTPException(status_code=500, detail=str(e))

        @router.post("/n8n/webhook")
        async def n8n_webhook(payload: dict, services=Depends(get_services)):
            return await _handle_payload(payload, services)

        @router.post("/evaluar")
        async def evaluar(payload: dict, services=Depends(get_services)):
            return await _handle_payload(payload, services)

        return router
