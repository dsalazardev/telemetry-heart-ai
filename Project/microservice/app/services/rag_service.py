import hashlib
from logging import getLogger
from pathlib import Path

from langchain_core.embeddings import Embeddings
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = getLogger(__name__)


class RagService:
    def __init__(self, embedding: Embeddings, persist_dir: str, docs_dir: str, chunk_size: int = 800, chunk_overlap: int = 120, retrieval_k: int = 4):
        self.embedding = embedding
        self.persist_dir = Path(persist_dir)
        self.docs_dir = Path(docs_dir)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.retrieval_k = retrieval_k
        self.vectorstore: Chroma | None = None
        self.initialized = False

    def initialize(self):
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        if list(self.persist_dir.glob("*.parquet")):
            try:
                self.vectorstore = Chroma(
                    persist_directory=str(self.persist_dir),
                    embedding_function=self.embedding,
                )
                self.initialized = True
                logger.info("Vectorstore cargado desde %s", self.persist_dir)
                return
            except Exception:
                logger.info("No se pudo cargar vectorstore existente, reindexando")

        documents = []
        for md_file in sorted(self.docs_dir.glob("*.md")):
            try:
                loader = TextLoader(str(md_file), encoding="utf-8")
                docs = loader.load()
                for doc in docs:
                    doc.metadata["source"] = md_file.name
                    doc.metadata["section"] = "general"
                    doc.metadata["version"] = "demo-v1"
                documents.extend(docs)
                logger.info("Cargado: %s", md_file.name)
            except Exception as e:
                logger.error("Error cargando %s: %s", md_file.name, e)

        if not documents:
            logger.warning("No hay documentos para indexar")
            return

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " "],
        )
        chunks = splitter.split_documents(documents)
        for i, chunk in enumerate(chunks):
            chunk_id = hashlib.md5(chunk.page_content.encode()).hexdigest()[:12]
            chunk.metadata["chunk_id"] = f"chunk_{chunk_id}"

        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embedding,
            persist_directory=str(self.persist_dir),
        )
        self.initialized = True
        logger.info("Indexados %d chunks de %d documentos", len(chunks), len(documents))

    def retrieve(self, query: str, k: int | None = None) -> list[dict]:
        if not self.vectorstore or not self.initialized:
            logger.warning("RAG no inicializado")
            return []
        k = k or self.retrieval_k
        try:
            docs = self.vectorstore.similarity_search_with_score(query, k=k)
            return [
                {
                    "content": doc.page_content[:200],
                    "metadata": doc.metadata,
                    "score": round(float(score), 4),
                }
                for doc, score in docs
            ]
        except Exception as e:
            logger.error("Error en retrieval: %s", e)
            return []
