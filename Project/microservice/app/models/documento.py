from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Float
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY

if TYPE_CHECKING:
    from app.models.prediccion import Prediccion

class Documento(SQLModel, table=True):
    __tablename__ = "documentos"

    id: Optional[int] = Field(default=None, primary_key=True)
    titulo: str = Field(..., description="Titulo del documento clinico")
    contenido: str = Field(..., description="Texto completo")
    embedding: Optional[List[float]] = Field(
        default=None,
        sa_column=Column(PG_ARRAY(Float, dimensions=1))
    )
    fuente: str = Field(..., description="Origen del documento")
    fechaIndexacion: datetime = Field(default_factory=datetime.utcnow)
    activo: bool = Field(default=True, description="Disponible para RAG?")
    prediccion_id: Optional[int] = Field(default=None, foreign_key="predicciones.id")

    prediccion: Optional["Prediccion"] = Relationship(
        back_populates="documentos",
        sa_relationship_kwargs={"lazy": "selectin"}
    )

    def buscarSimilares(self, query: str) -> List["Documento"]:
        from app.services.rag_service import RAGService
        rag = RAGService()
        return rag.query(query)
