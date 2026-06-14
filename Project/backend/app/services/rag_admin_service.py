import httpx
from datetime import date
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.settings import settings
from app.models.patologia import Historial, Patologia


def _format_historial_doc(h: Historial, p: Patologia) -> dict:
    fecha_str = h.fechaDiagnostico.isoformat() if isinstance(h.fechaDiagnostico, date) else str(h.fechaDiagnostico)
    paciente_anonimo = f"P-{str(h.paciente_id).zfill(4)}"
    factor_cardiaco = "sí" if p.factorRiesgoCardiaco else "no"

    contenido = (
        f"## Historial Clínico Anonimizado\n\n"
        f"**Patología:** {p.nombre}\n"
        f"**Categoría:** {p.categoria}\n"
        f"**Código CIE-11:** {p.codigoCie11}\n"
        f"**Severidad:** {h.nivelSeveridad}\n"
        f"**Controlada:** {'sí' if h.controlada else 'no'}\n"
        f"**Factor de riesgo cardíaco:** {factor_cardiaco}\n"
        f"**Fecha diagnóstico:** {fecha_str}\n"
        f"**Tratamiento actual:** {h.tratamientoActual or 'no registrado'}\n"
    )
    if h.observaciones:
        contenido += f"**Observaciones:** {h.observaciones}\n"
    contenido += (
        f"\nPaciente anónimo: {paciente_anonimo}.\n"
        f"Peso en el modelo de riesgo: {p.pesoRiesgoModelo}.\n"
    )

    return {
        "titulo": f"Historial {paciente_anonimo} - {p.nombre}",
        "contenido": contenido,
        "fuente": "historial_clinico_bd",
        "categoria": "historial_clinico",
        "metadata_extra": {
            "paciente_anonimo": paciente_anonimo,
            "fecha": fecha_str,
            "severidad": h.nivelSeveridad,
            "patologia": p.nombre,
            "factor_cardiaco": p.factorRiesgoCardiaco,
            "historial_id": h.id,
        },
    }


async def fetch_historiales_for_rag(
    db: AsyncSession,
    limit: int = 100,
    only_cardiaco: bool = False,
) -> List[dict]:
    stmt = (
        select(Historial, Patologia)
        .join(Patologia, Historial.patologia_id == Patologia.id)
        .order_by(Historial.fechaDiagnostico.desc())
        .limit(limit)
    )
    if only_cardiaco:
        stmt = stmt.where(Patologia.factorRiesgoCardiaco == True)  # noqa: E712

    result = await db.execute(stmt)
    rows = result.all()
    return [_format_historial_doc(h, p) for h, p in rows]


async def sync_historiales_to_rag(
    db: AsyncSession,
    limit: int = 100,
    only_cardiaco: bool = False,
    dry_run: bool = False,
) -> dict:
    docs = await fetch_historiales_for_rag(db, limit=limit, only_cardiaco=only_cardiaco)

    if dry_run:
        return {
            "status": "dry_run",
            "would_index": len(docs),
            "sample_titles": [d["titulo"] for d in docs[:3]],
        }

    if not docs:
        return {"status": "ok", "indexed": 0, "failed": 0, "total_chunks": 0}

    payload = {"documents": docs}
    headers = {"Authorization": f"Bearer {settings.INTERNAL_TOKEN}"} if hasattr(settings, "INTERNAL_TOKEN") and settings.INTERNAL_TOKEN else {}

    url = f"{settings.MICROSERVICE_URL.rstrip('/')}/rag/documents/bulk"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
        except httpx.TimeoutException:
            return {"status": "error", "error": "microservice_timeout", "would_index": len(docs)}
        except httpx.HTTPStatusError as e:
            return {
                "status": "error",
                "error": f"microservice_http_{e.response.status_code}",
                "detail": e.response.text,
                "would_index": len(docs),
            }
        except Exception as e:
            return {"status": "error", "error": "connection_error", "detail": str(e)}

    return {
        "status": "ok",
        "indexed": result.get("added", 0),
        "failed": result.get("failed", 0),
        "total_chunks": result.get("total_chunks", 0),
        "would_index": len(docs),
    }
