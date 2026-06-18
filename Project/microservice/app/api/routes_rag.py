from logging import getLogger

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.dependencies import verify_internal_token
from app.schemas.rag import (
    RagBulkRequest,
    RagBulkResponse,
    RagDocumentRequest,
    RagDocumentSummary,
    RagDocumentUpdate,
    RagListResponse,
    RagReindexResponse,
)

logger = getLogger(__name__)
router = APIRouter(
    prefix="/rag",
    tags=["rag"],
    dependencies=[Depends(verify_internal_token)],
)


def _rag(request: Request):
    rag = request.app.state.services.rag
    if not rag.is_ready():
        raise HTTPException(status_code=503, detail="RAG no disponible (ChromaDB no inicializado)")
    return rag


@router.post("/documents", status_code=201)
async def create_document(req: RagDocumentRequest, request: Request):
    """Indexa un documento clínico en ChromaDB."""
    try:
        return _rag(request).add_document(
            titulo=req.titulo,
            contenido=req.contenido,
            fuente=req.fuente,
            categoria=req.categoria,
            metadata_extra=req.metadata_extra,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/documents/bulk", response_model=RagBulkResponse)
async def create_documents_bulk(req: RagBulkRequest, request: Request):
    """Indexación masiva. Consumido por el sync de historiales del backend."""
    results = _rag(request).add_documents([d.model_dump() for d in req.documents])
    added = sum(1 for r in results if "error" not in r)
    failed = len(results) - added
    total_chunks = sum(r.get("chunks_count", 0) for r in results if "error" not in r)
    return RagBulkResponse(added=added, failed=failed, total_chunks=total_chunks)


@router.get("/documents", response_model=RagListResponse)
async def list_documents(request: Request, limit: int = 50, offset: int = 0):
    """Lista documentos indexados (agrupados por doc_id)."""
    return _rag(request).list_documents(limit=limit, offset=offset)


@router.get("/documents/{doc_id}", response_model=RagDocumentSummary)
async def get_document(doc_id: str, request: Request):
    doc = _rag(request).get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return doc


@router.put("/documents/{doc_id}")
async def update_document(doc_id: str, req: RagDocumentUpdate, request: Request):
    """Actualiza un documento. Con ``contenido`` se re-embebe; si no, sólo metadatos."""
    result = _rag(request).update_document(
        doc_id=doc_id,
        titulo=req.titulo,
        contenido=req.contenido,
        fuente=req.fuente,
        categoria=req.categoria,
        metadata_extra=req.metadata_extra,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return result


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, request: Request):
    removed = _rag(request).remove_document(doc_id)
    if removed == 0:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return {"status": "deleted", "doc_id": doc_id, "chunks_removed": removed}


@router.post("/reindex", response_model=RagReindexResponse)
async def reindex(request: Request):
    """Reconstruye el índice desde los .md de clinical_docs, descartando lo anterior."""
    result = _rag(request).reindex()
    return RagReindexResponse(
        documents_indexed=result["documents_indexed"],
        chunks_count=result["chunks_count"],
    )
