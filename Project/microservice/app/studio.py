import os
from logging import getLogger

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.resolver import create_llm, create_embeddings
from app.services.risk_engine import RiskEngine
from app.services.rag_service import RAGService
from app.services.triage_priority_service import TriagePriorityService
from app.services.ml_priority_service import MLPriorityService
from app.agents.clinical_subgraph import ClinicalGraph

logger = getLogger(__name__)
setup_logging()

os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key or "")
os.environ.setdefault("LANGCHAIN_API_KEY", settings.langsmith_api_key or "")
os.environ.setdefault("LANGCHAIN_TRACING_V2", "true" if settings.langsmith_trace_v2 else "false")
os.environ.setdefault("LANGCHAIN_PROJECT", settings.langsmith_project)

_llm = create_llm(settings)
_embeddings = create_embeddings(settings)
_risk_engine = RiskEngine(settings.weights_path)
_rag = RAGService(
    embedding=_embeddings,
    persist_dir=settings.vectorstore_path,
    docs_dir=settings.clinical_docs_path,
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap,
    retrieval_k=settings.retrieval_k,
    retrieval_max_length=settings.retrieval_max_length,
)
if settings.priority_strategy == "ml":
    ml = MLPriorityService(settings.model_path)
    if ml.loaded:
        _triage_priority = ml
        logger.info("Studio: priorización ML (%s)", ml.version)
    else:
        _triage_priority = TriagePriorityService(settings.triage_weights_path)
        logger.warning("Studio: priority_strategy=ml pero model.pkl no cargó; usando PSO")
else:
    _triage_priority = TriagePriorityService(settings.triage_weights_path)

_clinical = ClinicalGraph(_llm, _risk_engine, _rag, _triage_priority)

clinical_graph = _clinical.graph

logger.info("LangGraph Studio graph ready: clinical")
