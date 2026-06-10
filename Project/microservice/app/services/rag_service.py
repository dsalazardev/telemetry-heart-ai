import hashlib
import time
from functools import lru_cache
from logging import getLogger
from pathlib import Path

from langchain_core.embeddings import Embeddings
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = getLogger(__name__)

_CHROMA_DB_FILE = "chroma.sqlite3"


class RagService:
    def __init__(
        self,
        embedding: Embeddings,
        persist_dir: str,
        docs_dir: str,
        chunk_size: int = 800,
        chunk_overlap: int = 120,
        retrieval_k: int = 4,
        separators: list[str] | None = None,
        retrieval_max_length: int = 2000,
    ):
        self.embedding = embedding
        self.persist_dir = Path(persist_dir)
        self.docs_dir = Path(docs_dir)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.retrieval_k = retrieval_k
        self.separators = separators or ["\n## ", "\n### ", "\n\n", "\n", ". ", " "]
        self.retrieval_max_length = retrieval_max_length
        self.vectorstore: Chroma | None = None
        self.initialized = False
        self.chunk_count: int = 0
        self.doc_count: int = 0

    def _chroma_db_exists(self) -> bool:
        return (self.persist_dir / _CHROMA_DB_FILE).exists()

    def initialize(self):
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        if self._chroma_db_exists():
            try:
                self.vectorstore = Chroma(
                    persist_directory=str(self.persist_dir),
                    embedding_function=self.embedding,
                )
                self.initialized = True
                self.chunk_count = self.vectorstore._collection.count()
                logger.info(
                    "Vectorstore cargado desde %s (%d chunks)",
                    self.persist_dir, self.chunk_count,
                )
                return
            except Exception as e:
                logger.warning("No se pudo cargar vectorstore existente: %s", e)

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
            separators=self.separators,
        )
        chunks = splitter.split_documents(documents)
        for chunk in chunks:
            chunk_id = hashlib.md5(chunk.page_content.encode()).hexdigest()[:12]
            chunk.metadata["chunk_id"] = f"chunk_{chunk_id}"

        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embedding,
            persist_directory=str(self.persist_dir),
        )
        self.initialized = True
        self.chunk_count = len(chunks)
        self.doc_count = len(documents)
        logger.info("Indexados %d chunks de %d documentos", self.chunk_count, self.doc_count)

    def _get_cached(self, query: str, k: int | None = None) -> list[dict]:
        """Cache interno: misma query devuelve mismo resultado si hay pocos cambios."""
        return self._retrieve_impl(query, k)

    def retrieve(self, query: str, k: int | None = None) -> list[dict]:
        """Síncrono para uso interno. Preferir retrieve_async en contexts async."""
        return self._retrieve_impl(query, k)

    async def retrieve_async(self, query: str, k: int | None = None) -> list[dict]:
        """Versión async que no bloquea el event loop."""
        import asyncio
        return await asyncio.to_thread(self._retrieve_impl, query, k)

    def _retrieve_impl(self, query: str, k: int | None = None) -> list[dict]:
        if not self.vectorstore or not self.initialized:
            logger.warning("RAG no inicializado")
            return []
        k = k or self.retrieval_k
        try:
            docs = self.vectorstore.similarity_search_with_score(query, k=k)
            return [
                {
                    "content": doc.page_content[:self.retrieval_max_length],
                    "metadata": doc.metadata,
                    "score": round(float(score), 4),
                }
                for doc, score in docs
            ]
        except Exception as e:
            logger.error("Error en retrieval: %s", e)
            return []
