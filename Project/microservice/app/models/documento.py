from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, ARRAY, Float
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY

class Documento(SQLModel, table=True):
    __tablename__ = "documentos"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    titulo: str = Field(..., description="Título del documento clínico")
    contenido: str = Field(..., description="Texto completo")
    embedding: Optional[List[float]] = Field(
        default=None,
        sa_column=Column(PG_ARRAY(Float, dimensions=1))  # ARRAY Float(384)
    )
    fuente: str = Field(..., description="Origen del documento")
    fechaIndexacion: datetime = Field(default_factory=datetime.utcnow)
    activo: bool = Field(default=True, description="¿Disponible para RAG?")
    prediccion_id: Optional[int] = Field(default=None, foreign_key="predicciones.id")
    
    prediccion: Optional["Prediccion"] = Relationship()
    
    def buscarSimilares(self, query: str) -> List["Documento"]:
        """Delegado a RAGService"""
        from app.services.rag_service import RAGService
        rag = RAGService()
        return rag.query(query)
