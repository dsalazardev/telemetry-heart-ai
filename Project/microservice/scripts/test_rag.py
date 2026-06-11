import os
from app.services.rag_service import RAGService

def test_rag_service():
    """Test RAGService with a sample query"""
    rag = RAGService()
    
    # Add test document
    rag.add_documents([{
        "titulo": "Test",
        "contenido": "El riesgo cardiovascular aumenta con la edad y el colesterol elevado.",
        "fuente": "test",
        "fechaIndexacion": "2026-06-10",
        "activo": True
    }])
    
    # Query
    results = rag.query("¿Qué aumenta el riesgo cardiovascular?", n_results=3)
    print(f"Found {len(results)} results")
    for r in results:
        print(f"- {r['content'][:50]}... (distance: {r['distance']:.4f})")
    
    return results

if __name__ == "__main__":
    test_rag_service()
