from __future__ import annotations

from typing import Optional, Dict
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import JSON

class Adapter(SQLModel, table=True):
    __tablename__ = "adapters"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    proveedor: str = Field(..., description="n8n | langchain | manual")
    endpoint: str = Field(..., description="URL del webhook o endpoint")
    flujo: Optional[Dict] = Field(default=None, sa_type=JSON)
    token: str = Field(..., description="Auth token si aplica")
    activo: bool = Field(default=True, description="¿Activo?")
    fechaCreacion: datetime = Field(default_factory=datetime.utcnow)
    
    def ejecutarFlujo(self, triggerTipo: str, payload: Dict) -> Dict:
        """Delegado a WorkflowService"""
        from app.services.workflow_service import WorkflowService
        service = WorkflowService()
        return service.ejecutar_flujo(self, triggerTipo, payload)
    
    def notificarUrgencia(self, medico_id: int, mensaje: str) -> bool:
        """Delegado a WorkflowService"""
        from app.services.workflow_service import WorkflowService
        service = WorkflowService()
        return service.notificar_urgencia(self, medico_id, mensaje)
