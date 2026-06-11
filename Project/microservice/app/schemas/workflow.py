from typing import Optional, Dict
from pydantic import BaseModel

class WorkflowTrigger(BaseModel):
    adapter_id: int
    payload: Dict

class WorkflowResponse(BaseModel):
    status: str
    result: Optional[Dict] = None
    error: Optional[str] = None
