from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_medico
from app.services.rag_admin_service import sync_historiales_to_rag, fetch_historiales_for_rag
from app.models.usuario import Usuario


router = APIRouter()


class SyncHistorialesResponse(BaseModel):
    status: str
    indexed: int | None = None
    failed: int | None = None
    total_chunks: int | None = None
    would_index: int | None = None
    error: str | None = None
    detail: str | None = None
    sample_titles: list[str] | None = None


@router.post("/admin/rag/sync-historiales", response_model=SyncHistorialesResponse)
async def sync_historiales(
    limit: int = Query(100, ge=1, le=500),
    only_cardiaco: bool = Query(False),
    dry_run: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_medico),
):
    return await sync_historiales_to_rag(
        db=db,
        limit=limit,
        only_cardiaco=only_cardiaco,
        dry_run=dry_run,
    )


@router.get("/admin/rag/preview-historiales", response_model=list[dict])
async def preview_historiales(
    limit: int = Query(10, ge=1, le=50),
    only_cardiaco: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(get_current_medico),
):
    return await fetch_historiales_for_rag(
        db=db,
        limit=limit,
        only_cardiaco=only_cardiaco,
    )
