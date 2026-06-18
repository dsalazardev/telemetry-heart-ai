from typing import Any, Literal

from pydantic import BaseModel, Field


class RagDocumentRequest(BaseModel):
    """Payload para indexar un documento clínico en ChromaDB."""

    titulo: str = Field(..., min_length=1, max_length=256)
    contenido: str = Field(..., min_length=1)
    fuente: str | None = None
    categoria: str | None = None
    metadata_extra: dict[str, Any] | None = None


class RagBulkRequest(BaseModel):
    """Payload para indexación masiva (usado por el sync de historiales del backend)."""

    documents: list[RagDocumentRequest] = Field(..., min_length=1)


class RagDocumentUpdate(BaseModel):
    """Campos opcionales para actualizar un documento existente.

    Si ``contenido`` viene, el documento se re-fragmenta y re-embebe; si no,
    sólo se actualizan los metadatos.
    """

    titulo: str | None = None
    contenido: str | None = None
    fuente: str | None = None
    categoria: str | None = None
    metadata_extra: dict[str, Any] | None = None


class RagDocumentSummary(BaseModel):
    doc_id: str
    titulo: str
    fuente: str | None = None
    categoria: str | None = None
    fecha_indexacion: str | None = None
    chunks_count: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class RagListResponse(BaseModel):
    total: int
    documents: list[RagDocumentSummary]


class RagBulkResponse(BaseModel):
    status: Literal["ok"] = "ok"
    added: int
    failed: int
    total_chunks: int


class RagReindexResponse(BaseModel):
    status: Literal["reindexed"] = "reindexed"
    documents_indexed: int
    chunks_count: int
