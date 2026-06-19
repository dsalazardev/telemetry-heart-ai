import os
import glob
from app.services.rag_service import RAGService


def bootstrap_chroma():
    """Load clinical knowledge base into ChromaDB"""
    rag = RAGService()

    kb_dir = "./data/knowledge_base"
    if not os.path.exists(kb_dir):
        print(f"[WARN] Knowledge base directory not found: {kb_dir}")
        return

    # Read all markdown files
    documents = []
    for filepath in glob.glob(os.path.join(kb_dir, "*.md")):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        documents.append({
            "titulo": os.path.basename(filepath).replace('.md', ''),
            "contenido": content,
            "fuente": "clinical_kb",
            "fechaIndexacion": "2026-06-10",
            "activo": True
        })

    if documents:
        rag.add_documents(documents)
        print(f"[OK] Loaded {len(documents)} documents into ChromaDB")
    else:
        print("[WARN] No documents found in knowledge base")

    stats = rag.get_collection_stats()
    print(f"[STATS] Collection stats: {stats}")


if __name__ == "__main__":
    bootstrap_chroma()