import httpx
from typing import Dict, Optional
from app.models.adapter import Adapter

class WorkflowService:
    async def ejecutar_flujo(self, adapter: Adapter, trigger_tipo: str, payload: Dict) -> Dict:
        """Execute workflow via adapter"""
        if not adapter.activo:
            raise ValueError("Adapter is inactive")
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {}
                if adapter.token:
                    headers["Authorization"] = f"Bearer {adapter.token}"
                
                response = await client.post(
                    adapter.endpoint,
                    json={
                        "trigger_type": trigger_tipo,
                        "payload": payload,
                        "provider": adapter.proveedor
                    },
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def notificar_urgencia(self, adapter: Adapter, medico_id: int, mensaje: str) -> bool:
        """Send urgency notification"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {}
                if adapter.token:
                    headers["Authorization"] = f"Bearer {adapter.token}"
                
                response = await client.post(
                    adapter.endpoint,
                    json={
                        "type": "urgencia",
                        "medico_id": medico_id,
                        "mensaje": mensaje
                    },
                    headers=headers,
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception:
            return False
