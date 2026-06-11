import os
import time
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from app.core.settings import settings

class RAGService:
    def __init__(self):
        self.chroma_path = settings.CHROMA_PATH
        self.model = None
        self.collection = None
        self._init_embedding_model()
        self._init_chroma()
    
    def _init_embedding_model(self):
        """Initialize SentenceTransformer model"""
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.model = SentenceTransformer(model_name)
        print(f"[OK] Embedding model loaded: {model_name}")
    
    def _init_chroma(self):
        """Initialize ChromaDB PersistentClient"""
        try:
            import chromadb
            self.client = chromadb.PersistentClient(path=self.chroma_path)
            self.collection = self.client.get_or_create_collection(
                name="clinical_knowledge",
                metadata={"hnsw:space": "cosine"}
            )
            print(f"[OK] ChromaDB collection ready: clinical_knowledge")
        except Exception as e:
            print(f"[WARN] ChromaDB init error: {e}")
            self.client = None
            self.collection = None
    
    def add_documents(self, documents: List[Dict]):
        """Add documents to vector store"""
        if not self.collection:
            return
        
        texts = [doc["contenido"] for doc in documents]
        embeddings = self.model.encode(texts).tolist()
        
        ids = [f"doc_{i}" for i in range(len(documents))]
        metadatas = [{
            "titulo": doc.get("titulo", ""),
            "fuente": doc.get("fuente", ""),
            "fechaIndexacion": doc.get("fechaIndexacion", ""),
            "activo": doc.get("activo", True)
        } for doc in documents]
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
    
    def query(self, query_text: str, n_results: int = 5) -> List[Dict]:
        """Query the vector store"""
        if not self.collection:
            return []
        
        start = time.time()
        query_embedding = self.model.encode([query_text]).tolist()
        
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        elapsed = (time.time() - start) * 1000
        print(f"[SEARCH] RAG query: {elapsed:.2f}ms")
        
        documents = []
        for i in range(len(results["ids"][0])):
            documents.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })
        
        return documents
    
    def get_collection_stats(self) -> Dict:
        if not self.collection:
            return {"count": 0}
        return {"count": self.collection.count()}
    
    def is_ready(self) -> bool:
        return self.collection is not None
