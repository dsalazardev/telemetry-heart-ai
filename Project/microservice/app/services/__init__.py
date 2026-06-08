import json
from logging import getLogger
from pathlib import Path

from app.core.config import Settings
from app.models import create_embeddings, create_llm
from app.services.agent_service import AgentService
from app.services.metrics_service import MetricsService
from app.services.rag_service import RagService
from app.services.risk_engine import RiskEngine

logger = getLogger(__name__)


class Services:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.risk_engine = RiskEngine(settings.weights_path)

        llm = create_llm(settings)
        embeddings = create_embeddings(settings)

        self.rag = RagService(
            embedding=embeddings,
            persist_dir=settings.vectorstore_path,
            docs_dir=settings.clinical_docs_path,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            retrieval_k=settings.retrieval_k,
        )
        self.agent = AgentService(
            llm=llm,
            risk_engine=self.risk_engine,
            rag=self.rag,
        )
        self.metrics = MetricsService()

    async def initialize(self):
        weights_exist = Path(self.settings.weights_path).exists()
        if weights_exist:
            logger.info("Pesos cargados desde %s", self.settings.weights_path)
        else:
            logger.warning(
                "No se encontraron pesos optimizados en %s, usando baseline",
                self.settings.weights_path,
            )

        docs_exist = list(Path(self.settings.clinical_docs_path).glob("*.md"))
        if docs_exist:
            try:
                self.rag.initialize()
                logger.info("RAG inicializado con %d documentos", len(docs_exist))
            except Exception as e:
                logger.warning("Error inicializando RAG: %s", e)
        else:
            logger.warning(
                "No hay documentos clínicos en %s, RAG desactivado",
                self.settings.clinical_docs_path,
            )

    @property
    def rag_loaded(self) -> bool:
        return self.rag.initialized

    @property
    def weights_loaded(self) -> bool:
        return Path(self.settings.weights_path).exists()
