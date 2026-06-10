from logging import getLogger
from pathlib import Path

from app.core.config import Settings
from app.core.langsmith import get_client
from app.models import create_embeddings, create_llm
from app.services.metrics_service import MetricsService
from app.services.rag_service import RagService
from app.services.risk_engine import RiskEngine
from app.agents import load_agents

logger = getLogger(__name__)


class Services:
    def __init__(self, settings: Settings):
        self.settings = settings

        self.risk_engine = RiskEngine(
            settings.weights_path,
            config={"clinical_config_path": settings.clinical_config_path} if hasattr(settings, "clinical_config_path") else None,
        )
        llm = create_llm(settings)
        embeddings = create_embeddings(settings)

        if settings.embedding_provider == "fake":
            logger.warning(
                "Embeddings FAKE — el RAG devuelve resultados aleatorios. "
                "Configura embedding_provider=openai o huggingface en .env"
            )

        separators = [s.strip() for s in getattr(settings, "chunk_separators", "").split(",") if s.strip()]
        self.rag = RagService(
            embedding=embeddings,
            persist_dir=settings.vectorstore_path,
            docs_dir=settings.clinical_docs_path,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            retrieval_k=settings.retrieval_k,
            separators=separators or None,
            retrieval_max_length=settings.retrieval_max_length,
        )
        self.llm = llm
        self.weights_path = settings.weights_path

        self.agents = load_agents(self)

        for name, agent in self.agents.items():
            setattr(self, name if name.endswith("_graph") else f"{name}_graph", agent)

        self.metrics = MetricsService()

        ls_client = get_client()
        if ls_client:
            logger.info("LangSmith conectado: proyecto %s", settings.langsmith_project)

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
