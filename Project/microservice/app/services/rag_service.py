import hashlib
import os
import time
from functools import lru_cache
from logging import getLogger
from pathlib import Path
from typing import List, Dict

from sentence_transformers import SentenceTransformer
from app.core.settings import settings

logger = getLogger(__name__)

_CHROMA_DB_FILE = "chroma.sqlite3"


class RAGService:
    def __init__(
        self,
        embedding=None,
        persist_dir=None,
        docs_dir=None,
        chunk_size=800,
        chunk_overlap=120,
        retrieval_k=4,
        separators=None,
        retrieval_max_length=2000,
    ):
        self.chroma_path = persist_dir or settings.CHROMA_PATH
        self.persist_dir = Path(self.chroma_path)
        self.docs_dir = Path(docs_dir) if docs_dir else (
            Path(__file__).resolve().parent.parent.parent / "data" / "knowledge_base"
        )
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.retrieval_k = retrieval_k
        self.separators = separators or ["\n## ", "\n### ", "\n\n", "\n", ". ", " "]
        self.retrieval_max_length = retrieval_max_length
        self.model = None
        self.collection = None
        self.client = None
        self.vectorstore = None
        self.initialized = False
        self.chunk_count = 0
        self.doc_count = 0
        self._init_embedding_model()
        self._init_chroma()

    def _init_embedding_model(self):
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded: %s", model_name)

    def _init_chroma(self):
        try:
            import chromadb
            self.client = chromadb.PersistentClient(path=self.chroma_path)
            self.collection = self.client.get_or_create_collection(
                name="clinical_knowledge",
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("ChromaDB collection ready: clinical_knowledge")
        except Exception as e:
            logger.warning("ChromaDB init error: %s", e)
            self.client = None
            self.collection = None

    def _chroma_db_exists(self) -> bool:
        return (self.persist_dir / _CHROMA_DB_FILE).exists()

    def initialize(self):
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        if self._chroma_db_exists():
            self.chunk_count = self.collection.count() if self.collection else 0
            self.initialized = True
            logger.info(
                "Vectorstore cargado desde %s (%d chunks)",
                self.persist_dir, self.chunk_count,
            )
            return

        documents = []
        for md_file in sorted(self.docs_dir.glob("*.md")):
            try:
                content = md_file.read_text(encoding="utf-8")
                documents.append({
                    "contenido": content,
                    "titulo": md_file.stem,
                    "fuente": md_file.name,
                    "fechaIndexacion": "",
                    "activo": True,
                })
                logger.info("Cargado: %s", md_file.name)
            except Exception as e:
                logger.error("Error cargando %s: %s", md_file.name, e)

        if not documents:
            logger.warning("No hay documentos para indexar")
            return

        for i, doc in enumerate(documents):
            text = doc["contenido"]
            emb = self.model.encode([text]).tolist()
            meta = {
                "titulo": doc.get("titulo", ""),
                "fuente": doc.get("fuente", ""),
                "fechaIndexacion": doc.get("fechaIndexacion", ""),
                "activo": doc.get("activo", True),
            }
            self.collection.add(
                ids=[f"doc_{i}"],
                embeddings=emb,
                documents=[text],
                metadatas=[meta],
            )

        self.initialized = True
        self.chunk_count = self.collection.count() if self.collection else 0
        self.doc_count = len(documents)
        logger.info("Indexados %d documentos", self.doc_count)

    def add_documents(self, documents: List[Dict]):
        if not self.collection:
            return

        texts = [doc["contenido"] for doc in documents]
        embeddings = self.model.encode(texts).tolist()

        ids = [f"doc_{i}" for i in range(len(documents))]
        metadatas = [{
            "titulo": doc.get("titulo", ""),
            "fuente": doc.get("fuente", ""),
            "fechaIndexacion": doc.get("fechaIndexacion", ""),
            "activo": doc.get("activo", True),
        } for doc in documents]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        self.chunk_count = self.collection.count()

    def query(self, query_text: str, n_results: int = 5) -> List[Dict]:
        """Query the vector store"""
        if not self.collection:
            return []

        start = time.time()
        query_embedding = self.model.encode([query_text]).tolist()

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        elapsed = (time.time() - start) * 1000
        logger.debug("RAG query: %.2fms", elapsed)

        documents = []
        for i in range(len(results["ids"][0])):
            documents.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })

        return documents

    def retrieve(self, query: str, k: int | None = None) -> list[dict]:
        k = k or self.retrieval_k
        results = self.query(query, n_results=k)
        return [
            {
                "content": r["content"][:self.retrieval_max_length],
                "metadata": r["metadata"],
                "score": round(1.0 - r.get("distance", 0), 4),
            }
            for r in results
        ]

    async def retrieve_async(self, query: str, k: int | None = None) -> list[dict]:
        import asyncio
        return await asyncio.to_thread(self.retrieve, query, k)

    def get_collection_stats(self) -> Dict:
        if not self.collection:
            return {"count": 0}
        return {"count": self.collection.count()}

    def is_ready(self) -> bool:
        return self.collection is not None
