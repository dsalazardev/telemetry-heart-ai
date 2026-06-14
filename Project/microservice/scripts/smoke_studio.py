"""Smoke test del microservicio: clinical graph + @tool PSO.

Ejecutar desde Project/microservice/:
    PYTHONPATH=. python scripts/smoke_studio.py
"""
import asyncio
import json
import os
from pathlib import Path

from app.agents.clinical_subgraph import ClinicalGraph
from app.core.config import settings
from app.core.resolver import create_embeddings, create_llm
from app.schemas.prediction import PredictionRequest
from app.services.rag_service import RAGService
from app.services.risk_engine import RiskEngine
from app.services.triage_priority_service import TriagePriorityService
from app.tools import optimize_triage_priority_tool


def _export_env() -> None:
    if settings.openai_api_key:
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    if settings.langsmith_api_key:
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    if settings.langsmith_trace_v2:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
    if settings.langsmith_project:
        os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project


def _build_graph() -> ClinicalGraph:
    _export_env()
    llm = create_llm(settings)
    embeddings = create_embeddings(settings)
    risk_engine = RiskEngine(settings.weights_path)
    rag = RAGService(
        embedding=embeddings,
        persist_dir=settings.vectorstore_path,
        docs_dir=settings.clinical_docs_path,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        retrieval_k=settings.retrieval_k,
        retrieval_max_length=settings.retrieval_max_length,
    )
    rag.initialize()
    triage_priority = TriagePriorityService(settings.weights_path)
    return ClinicalGraph(llm, risk_engine, rag, triage_priority)


async def _test_clinical_critical():
    graph = _build_graph()
    req = PredictionRequest(
        paciente_id=1,
        heart_rate=160,
        spo2=82,
        systolic_bp=200,
        diastolic_bp=120,
        cholesterol=300,
        age=72,
        sex="M",
        chest_pain_type="asymptomatic",
        smoker=True,
        previous_condition=True,
        explain=False,
    )
    response = await graph.run(request=req)
    print("=== Caso crítico ===")
    print(f"  risk_score       = {response.risk_score}")
    print(f"  risk_level       = {response.risk_level}")
    print(f"  threshold_excd   = {response.threshold_exceeded}")
    print(f"  priority         = {response.priority}")
    print(f"  priority_level   = {response.priority_level}")
    print(f"  priority_score   = {response.priority_score}")
    print(f"  weights_version  = {response.weights_version}")
    print(f"  dominant_factors = {response.dominant_factors}")
    assert response.priority in ("BAJA", "MEDIA", "ALTA", "CRÍTICA")


async def _test_clinical_benign():
    graph = _build_graph()
    req = PredictionRequest(
        paciente_id=2,
        heart_rate=72,
        spo2=98,
        systolic_bp=118,
        diastolic_bp=76,
        cholesterol=180,
        age=35,
        sex="F",
        smoker=False,
        previous_condition=False,
        explain=False,
    )
    response = await graph.run(request=req)
    print("=== Caso benigno ===")
    print(f"  risk_score       = {response.risk_score}")
    print(f"  risk_level       = {response.risk_level}")
    print(f"  priority         = {response.priority}")
    assert response.priority in ("BAJA", "MEDIA", "ALTA", "CRÍTICA")


def _test_pso_tool():
    _export_env()
    print("=== @tool optimize_triage_priority_tool ===")
    result = optimize_triage_priority_tool.invoke({})
    print(f"  best_fitness     = {result.get('best_fitness')}")
    print(f"  n_generations    = {result.get('n_generations')}")
    print(f"  version          = {result.get('version')}")
    print(f"  weights (len)    = {len(result.get('weights', []))}")
    print(f"  thresholds       = {result.get('thresholds')}")
    print(f"  curve (len)      = {len(result.get('convergence_curve', []))}")
    print(f"  metrics          = {json.dumps(result.get('metrics', {}), indent=4)}")
    assert len(result["weights"]) == 7
    assert len(result["thresholds"]) == 3


if __name__ == "__main__":
    asyncio.run(_test_clinical_critical())
    asyncio.run(_test_clinical_benign())
    _test_pso_tool()
    print("\n✓ smoke_studio.py terminó sin errores")
