from logging import getLogger
from pathlib import Path

from app.core.config import Settings
from app.core.langsmith import get_client
from app.core.resolver import create_embeddings, create_llm
from app.services.metrics_service import MetricsService
from app.services.rag_service import RAGService
from app.services.risk_engine import RiskEngine
from app.services.triage_priority_service import TriagePriorityService
from app.agents import load_agents

logger = getLogger(__name__)

PRODUCTION_ENVIRONMENTS = {"demo", "prod", "evaluation"}


def validate_runtime_settings(settings: Settings) -> None:
    # Embeddings fake producen vectores aleatorios: el RAG devuelve basura.
    # Se bloquea antes del startup para evitar predicciones silenciosamente incorrectas.
    if settings.environment in PRODUCTION_ENVIRONMENTS:
        if settings.embedding_provider == "fake":
            raise RuntimeError(
                f"embedding_provider=fake no está permitido en environment={settings.environment}. "
                "Configure embedding_provider=huggingface u openai en .env"
            )


class Services:
    """Contenedor de todos los servicios del microservicio (singleton por instancia de FastAPI).

    Instancia y conecta: ``RiskEngine``, ``RAGService``, ``TriagePriorityService``,
    ``MetricsService``, LLM y los agentes LangGraph. ``initialize()`` es async
    y debe llamarse en el ``lifespan`` de FastAPI antes de servir requests.
    """

    def __init__(self, settings: Settings):
        self.settings = settings

        self.risk_engine = RiskEngine(settings.weights_path)
        llm = create_llm(settings)
        embeddings = create_embeddings(settings)

        validate_runtime_settings(settings)
        if settings.embedding_provider == "fake":
            logger.warning(
                "Embeddings FAKE — el RAG devuelve resultados aleatorios. "
                "Configura embedding_provider=openai o huggingface en .env"
            )

        separators = [s.strip() for s in getattr(settings, "chunk_separators", "").split(",") if s.strip()]
        self.rag = RAGService(
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

        self.triage_priority = TriagePriorityService(settings.triage_weights_path)

        self.agents = load_agents(self)

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

        logger.info(
            "STARTUP_CONFIG: embedding_provider=%s, embedding_model=%s, "
            "rag_collection=%s, documents_indexed=%d, llm_provider=%s, "
            "weights_version=%s, priority_loaded=%s, environment=%s",
            self.settings.embedding_provider,
            self.settings.embedding_model,
            "clinical_knowledge",
            getattr(self.rag, "doc_count", 0),
            self.settings.llm_provider,
            getattr(self.risk_engine, "version", "unknown"),
            self.triage_priority.loaded,
            self.settings.environment,
        )

    @property
    def rag_loaded(self) -> bool:
        return self.rag.initialized

    @property
    def weights_loaded(self) -> bool:
        return Path(self.settings.weights_path).exists()

    def is_ready(self) -> tuple[bool, list[str]]:
        errors = []
        if self.settings.embedding_provider == "fake":
            errors.append("embedding_provider=fake — no permitido en producción")
        if not self.rag_loaded:
            errors.append("RAG no cargado (sin documentos indexados)")
        if not self.weights_loaded:
            errors.append("Pesos optimizados no encontrados (usando baseline)")
        if not self.triage_priority.loaded:
            logger.warning(
                "TriagePriorityService en baseline (sin pesos PSO en %s)",
                self.settings.triage_weights_path,
            )
        return len(errors) == 0, errors
