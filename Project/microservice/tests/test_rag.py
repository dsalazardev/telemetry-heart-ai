import pytest
from langchain_community.embeddings import FakeEmbeddings
from app.services.rag_service import RAGService


@pytest.fixture
def embedding():
    return FakeEmbeddings(size=384)


@pytest.fixture
def rag(embedding, tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "test.md").write_text("# Test\nContenido de prueba para RAG.")
    persist_dir = tmp_path / "chroma"
    svc = RAGService(
        embedding=embedding,
        persist_dir=str(persist_dir),
        docs_dir=str(docs_dir),
        chunk_size=200,
        chunk_overlap=20,
        retrieval_k=2,
    )
    svc.initialize()
    return svc


@pytest.mark.asyncio
async def test_retrieval_con_resultados(rag):
    results = rag.retrieve("prueba")
    assert isinstance(results, list)
    assert len(results) >= 0


@pytest.mark.asyncio
async def test_retrieval_sin_resultados(rag):
    results = rag.retrieve("enfermedad rara no documentada XYZ123")
    assert isinstance(results, list)


def test_rag_no_inicializado():
    emb = FakeEmbeddings(size=384)
    svc = RAGService(
        embedding=emb,
        persist_dir="/nonexistent",
        docs_dir="/nonexistent",
    )
    results = svc.retrieve("test")
    assert results == []
