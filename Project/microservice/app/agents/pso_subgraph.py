import json
from logging import getLogger
from pathlib import Path

import numpy as np
import pandas as pd
from langgraph.graph import StateGraph, START, END
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from fastapi import APIRouter, Depends

from app.core.langgraph_state import PSOState
from app.core.langsmith import trace_node
from app.core.dependencies import get_services
from app.services.optimizers.pso import PSOOptimizer
from app.services.optimizers.base import OptimizerResult
from app.services.metrics_service import MetricsService
from app.services.risk_engine import RiskEngine
from app.agents.base import BaseAgent

logger = getLogger(__name__)

EXPLAIN_SYSTEM = """
Eres un experto en metaheurísticas aplicadas a riesgo cardiovascular.
Debes explicar los resultados de optimización PSO en lenguaje claro para un médico o ingeniero.
Incluye: qué mejoró, qué empeoró, qué significan los pesos, y recomendaciones.
"""


def _load_data(path: str) -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_csv(path)
    feature_cols = [c for c in df.columns if c != "risk_level"]
    X = df[feature_cols].values.astype(float)
    y = df["risk_level"].values
    return X, y


class PSOGraph(BaseAgent):
    name = "pso"
    def __init__(self, llm: BaseChatModel, risk_engine: RiskEngine, weights_path: str, data_path: str | None = None):
        self.llm = llm
        self.risk_engine = risk_engine
        self.weights_path = Path(weights_path)
        self.data_path = data_path or str(Path(weights_path).parent / "synthetic_cases.csv")
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        builder = StateGraph(PSOState)

        builder.add_node("load_data", self._load_data)
        builder.add_node("run_pso", self._run_pso)
        builder.add_node("evaluate_metrics", self._evaluate_metrics)
        builder.add_node("explain_results", self._explain_results)
        builder.add_node("export_weights", self._export_weights)
        builder.add_node("format_result", self._format_result)

        builder.add_edge(START, "load_data")
        builder.add_conditional_edges(
            "load_data",
            self._should_optimize,
            {True: "run_pso", False: "explain_results"},
        )
        builder.add_edge("run_pso", "evaluate_metrics")
        builder.add_conditional_edges(
            "evaluate_metrics",
            self._should_explain,
            {True: "explain_results", False: "export_weights"},
        )
        builder.add_edge("explain_results", "export_weights")
        builder.add_edge("export_weights", "format_result")
        builder.add_edge("format_result", END)

        return builder.compile()

    def _should_optimize(self, state: PSOState) -> bool:
        return state.get("action") == "optimize"

    def _should_explain(self, state: PSOState) -> bool:
        return state.get("action") in ("optimize", "explain")

    @trace_node("load_data")
    async def _load_data(self, state: PSOState) -> dict:
        try:
            if Path(self.data_path).exists():
                X, y = _load_data(self.data_path)
                return {"result": {"X_shape": X.shape, "y_distribution": dict(zip(*np.unique(y, return_counts=True)))}}
            return {"error": f"No se encuentra {self.data_path}"}
        except Exception as e:
            return {"error": str(e)}

    @trace_node("run_pso")
    async def _run_pso(self, state: PSOState) -> dict:
        try:
            X, y = _load_data(self.data_path)
            optimizer = PSOOptimizer(
                n_particles=state.get("n_particles", 30),
                max_iter=state.get("max_iter", 100),
            )
            result: OptimizerResult = optimizer.optimize(X, y)
            return {"result": result.model_dump()}
        except Exception as e:
            return {"error": str(e)}

    @trace_node("evaluate_metrics")
    async def _evaluate_metrics(self, state: PSOState) -> dict:
        try:
            X, y = _load_data(self.data_path)
            n = X.shape[1]
            baseline_w = np.ones(n) / n
            baseline_t = [0.40, 0.70]
            opt_w = np.array(state["result"]["weights"])
            opt_t = state["result"]["thresholds"]
            opt_b = state["result"].get("bias", 0.0)

            ms = MetricsService()
            comparison = ms.compare(X, y, baseline_w, baseline_t, opt_w, opt_t, 0.0, opt_b)
            return {"comparison": comparison}
        except Exception as e:
            return {"error": str(e)}

    @trace_node("explain_results")
    async def _explain_results(self, state: PSOState) -> dict:
        try:
            prompt = f"Resultados de optimización PSO:\n{json.dumps(state.get('result', {}), indent=2)}"
            if state.get("comparison"):
                prompt += f"\n\nComparación baseline vs optimizado:\n{json.dumps(state['comparison'], indent=2)}"

            messages = [SystemMessage(content=EXPLAIN_SYSTEM), HumanMessage(content=prompt)]
            response = await self.llm.ainvoke(messages)
            explanation = response.content if hasattr(response, "content") else str(response)
            return {"explanation": explanation}
        except Exception as e:
            return {"explanation": f"No se pudo generar explicación: {e}"}

    @trace_node("export_weights")
    async def _export_weights(self, state: PSOState) -> dict:
        if not state.get("result"):
            return {}
        r = state["result"]
        data = {
            "weights": r["weights"],
            "thresholds": r["thresholds"],
            "bias": r.get("bias", 0.0),
            "version": r.get("version", "pso-v1"),
            "metrics": state.get("comparison", {}),
        }
        self.weights_path.write_text(json.dumps(data, indent=2))
        logger.info("Pesos exportados a %s", self.weights_path)
        return {}

    @trace_node("format_result")
    async def _format_result(self, state: PSOState) -> dict:
        return {
            "result": state.get("result"),
            "comparison": state.get("comparison"),
            "explanation": state.get("explanation"),
        }

    async def run(self, action: str = "explain", n_particles: int = 30, max_iter: int = 100, **kwargs) -> dict:
        initial = PSOState(
            action=action,
            n_particles=n_particles,
            max_iter=max_iter,
            result=None,
            comparison=None,
            explanation=None,
            error=None,
        )
        result = await self.graph.ainvoke(initial)
        return {
            "result": result.get("result"),
            "comparison": result.get("comparison"),
            "explanation": result.get("explanation"),
        }

    @property
    def router(self) -> APIRouter:
        router = APIRouter(tags=["optimize"])

        @router.post("/optimize")
        async def optimize(action: str = "optimize", n_particles: int = 30, max_iter: int = 100,
                           services=Depends(get_services)):
            pso = services.agents.get("pso")
            if pso is None:
                return {"error": "pso agent no disponible"}
            try:
                return await pso.run(action=action, n_particles=n_particles, max_iter=max_iter)
            except Exception as e:
                logger.error("Error en /optimize: %s", e)
                return {"error": str(e), "action": action}

        return router
