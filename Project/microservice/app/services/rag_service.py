"""Servicio RAG sobre ChromaDB para recuperación de guías clínicas cardiovasculares.

Flujo de inicialización:
  1. Si ``chroma.sqlite3`` ya existe en ``persist_dir``, carga el índice existente.
  2. Si no, lee todos los ``.md`` de ``docs_dir``, los fragmenta y los indexa.

``retrieve()``/``retrieve_async()`` devuelven chunks ordenados por similitud coseno
(score = 1 − distancia). El agente ``ClinicalGraph`` filtra adicionalmente los
resultados con ``score >= MIN_RAG_SCORE`` antes de pasarlos al LLM.
"""
import time
import uuid
from datetime import datetime, timezone
from logging import getLogger
from pathlib import Path
from typing import List, Dict, Any

from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from app.core.config import settings

logger = getLogger(__name__)

_CHROMA_DB_FILE = "chroma.sqlite3"


class RAGService:
    """ChromaDB-backed retrieval service para conocimiento clínico cardiovascular.

    Soporta dos modos de embedding: proveedor LangChain (``Embeddings``) o
    ``SentenceTransformer`` como fallback. Los documentos se fragmentan con
    ``RecursiveCharacterTextSplitter`` y se almacenan en la colección
    ``clinical_knowledge`` con metadatos de trazabilidad (fuente, chunk_index, fecha).
    """

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
        self.chroma_path = persist_dir or settings.vectorstore_path
        self.persist_dir = Path(self.chroma_path)
        self.docs_dir = Path(docs_dir) if docs_dir else (
            Path(__file__).resolve().parent.parent / "data" / "clinical_docs"
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
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
        )
        self._init_embedding_model(embedding)
        self._init_chroma()

    def _init_embedding_model(self, embedding=None):
        if embedding is not None and isinstance(embedding, Embeddings):
            self.model = embedding
            logger.info("Embedding model: %s (via provider)", type(embedding).__name__)
        else:
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            self.model = SentenceTransformer(model_name)
            logger.info("Embedding model loaded: %s (fallback)", model_name)

    def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        if isinstance(self.model, Embeddings):
            return self.model.embed_documents(texts)
        return self.model.encode(texts).tolist()

    def _embed_query(self, query_text: str) -> List[float]:
        if isinstance(self.model, Embeddings):
            return self.model.embed_query(query_text)
        return self.model.encode([query_text]).tolist()[0]

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

    def _chunk_text(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []
        if len(text) <= self.chunk_size:
            return [text]
        return self._splitter.split_text(text)

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
                doc_id = uuid.uuid4().hex
                chunks = self._chunk_text(content)
                now_iso = datetime.now(timezone.utc).isoformat()
                for idx, chunk in enumerate(chunks):
                    documents.append({
                        "id": f"{doc_id}_chunk_{idx}",
                        "contenido": chunk,
                        "titulo": md_file.stem,
                        "fuente": md_file.name,
                        "doc_id": doc_id,
                        "chunk_index": idx,
                        "total_chunks": len(chunks),
                        "categoria": "guia_clinica",
                        "fechaIndexacion": now_iso,
                    })
                logger.info("Cargado: %s (%d chunks)", md_file.name, len(chunks))
            except Exception as e:
                logger.error("Error cargando %s: %s", md_file.name, e)

        if not documents:
            logger.warning("No hay documentos para indexar")
            return

        texts = [d["contenido"] for d in documents]
        embeddings = self._embed_texts(texts)
        ids = [d["id"] for d in documents]
        metadatas = [{
            "titulo": d["titulo"],
            "fuente": d["fuente"],
            "doc_id": d["doc_id"],
            "chunk_index": d["chunk_index"],
            "total_chunks": d["total_chunks"],
            "categoria": d["categoria"],
            "fechaIndexacion": d["fechaIndexacion"],
        } for d in documents]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        self.initialized = True
        self.chunk_count = self.collection.count() if self.collection else 0
        self.doc_count = len({d["doc_id"] for d in documents})
        logger.info("Indexados %d documentos (%d chunks)", self.doc_count, self.chunk_count)

    def add_document(
        self,
        titulo: str,
        contenido: str,
        fuente: str | None = None,
        categoria: str | None = None,
        metadata_extra: dict[str, Any] | None = None,
    ) -> dict:
        if not self.collection:
            raise RuntimeError("ChromaDB collection no inicializada")

        chunks = self._chunk_text(contenido)
        if not chunks:
            raise ValueError("El contenido no produjo chunks válidos")

        doc_id = uuid.uuid4().hex
        now_iso = datetime.now(timezone.utc).isoformat()
        chunk_ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        meta_base = {
            "titulo": titulo,
            "fuente": fuente or "",
            "doc_id": doc_id,
            "categoria": categoria or "general",
            "fechaIndexacion": now_iso,
        }
        metadatas = []
        for i, _ in enumerate(chunks):
            md = dict(meta_base)
            md["chunk_index"] = i
            md["total_chunks"] = len(chunks)
            if metadata_extra:
                for k, v in metadata_extra.items():
                    md[f"meta_{k}"] = v if isinstance(v, (str, int, float, bool)) else str(v)
            metadatas.append(md)

        embeddings = self._embed_texts(chunks)
        self.collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )
        self.chunk_count = self.collection.count()
        return {
            "doc_id": doc_id,
            "titulo": titulo,
            "fuente": fuente,
            "categoria": categoria,
            "chunks_count": len(chunks),
            "chunk_ids": chunk_ids,
            "fecha_indexacion": now_iso,
        }

    def add_documents(self, documents: List[Dict]) -> List[dict]:
        results = []
        for doc in documents:
            try:
                result = self.add_document(
                    titulo=doc.get("titulo", "sin_titulo"),
                    contenido=doc.get("contenido", ""),
                    fuente=doc.get("fuente"),
                    categoria=doc.get("categoria"),
                    metadata_extra=doc.get("metadata_extra"),
                )
                results.append(result)
            except Exception as e:
                logger.error("Error añadiendo documento: %s", e)
                results.append({"error": str(e), "titulo": doc.get("titulo")})
        return results

    def get_document(self, doc_id: str) -> dict | None:
        if not self.collection:
            return None
        try:
            results = self.collection.get(where={"doc_id": doc_id})
        except Exception as e:
            logger.error("Error en get_document: %s", e)
            return None

        ids = results.get("ids", [])
        if not ids:
            return None

        metadatas = results.get("metadatas", [])
        documents = results.get("documents", [])
        if not metadatas:
            return None

        first_meta = metadatas[0]
        return {
            "doc_id": doc_id,
            "titulo": first_meta.get("titulo", ""),
            "fuente": first_meta.get("fuente"),
            "categoria": first_meta.get("categoria"),
            "fecha_indexacion": first_meta.get("fechaIndexacion"),
            "chunks_count": len(ids),
            "chunk_ids": ids,
            "metadata": {
                k.removeprefix("meta_"): v
                for k, v in first_meta.items()
                if k.startswith("meta_")
            },
        }

    def list_documents(self, limit: int = 50, offset: int = 0) -> dict:
        if not self.collection:
            return {"total": 0, "documents": []}

        try:
            all_data = self.collection.get(include=["metadatas"])
        except Exception as e:
            logger.error("Error en list_documents: %s", e)
            return {"total": 0, "documents": []}

        all_ids = all_data.get("ids", [])
        all_metas = all_data.get("metadatas", [])

        grouped: dict[str, dict] = {}
        for cid, meta in zip(all_ids, all_metas):
            if not meta:
                continue
            doc_id = meta.get("doc_id")
            if not doc_id:
                continue
            if doc_id not in grouped:
                grouped[doc_id] = {
                    "doc_id": doc_id,
                    "titulo": meta.get("titulo", ""),
                    "fuente": meta.get("fuente"),
                    "categoria": meta.get("categoria"),
                    "fecha_indexacion": meta.get("fechaIndexacion"),
                    "chunks_count": 0,
                    "metadata": {
                        k.removeprefix("meta_"): v
                        for k, v in meta.items()
                        if k.startswith("meta_")
                    },
                }
            grouped[doc_id]["chunks_count"] += 1

        all_docs = list(grouped.values())
        total = len(all_docs)
        sliced = all_docs[offset:offset + limit]
        return {"total": total, "documents": sliced}

    def update_document(
        self,
        doc_id: str,
        titulo: str | None = None,
        contenido: str | None = None,
        fuente: str | None = None,
        categoria: str | None = None,
        metadata_extra: dict[str, Any] | None = None,
    ) -> dict | None:
        existing = self.get_document(doc_id)
        if not existing:
            return None

        if contenido is not None:
            self.remove_document(doc_id)
            return self.add_document(
                titulo=titulo or existing["titulo"],
                contenido=contenido,
                fuente=fuente if fuente is not None else existing["fuente"],
                categoria=categoria if categoria is not None else existing["categoria"],
                metadata_extra=metadata_extra or existing.get("metadata"),
            )
        else:
            if not self.collection:
                raise RuntimeError("ChromaDB collection no inicializada")

            update_meta = {
                "titulo": titulo or existing["titulo"],
                "fuente": fuente if fuente is not None else (existing["fuente"] or ""),
                "categoria": categoria if categoria is not None else (existing["categoria"] or "general"),
                "fechaIndexacion": datetime.now(timezone.utc).isoformat(),
            }
            if metadata_extra:
                for k, v in metadata_extra.items():
                    update_meta[f"meta_{k}"] = v if isinstance(v, (str, int, float, bool)) else str(v)

            for cid in existing["chunk_ids"]:
                self.collection.update(
                    ids=[cid],
                    metadatas=[update_meta],
                )
            return self.get_document(doc_id)

    def remove_document(self, doc_id: str) -> int:
        if not self.collection:
            return 0
        try:
            existing = self.collection.get(where={"doc_id": doc_id})
            ids_to_delete = existing.get("ids", [])
            if not ids_to_delete:
                return 0
            self.collection.delete(ids=ids_to_delete)
            self.chunk_count = self.collection.count()
            return len(ids_to_delete)
        except Exception as e:
            logger.error("Error en remove_document: %s", e)
            return 0

    def query(self, query_text: str, n_results: int = 5) -> List[Dict]:
        if not self.collection:
            return []

        start = time.time()
        query_embedding = [self._embed_query(query_text)]

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

    def add_document_from_file(self, *args, **kwargs):  # noqa: D401 — legacy stub
        raise NotImplementedError(
            "La carga de archivos dinámicos no está disponible en esta versión. "
            "Indexa documentos en el directorio configurado en `clinical_docs_path`."
        )
