from fastapi import APIRouter, HTTPException
from app.schemas.workflow import WorkflowTrigger, WorkflowResponse

router = APIRouter()

@router.post("/trigger", response_model=WorkflowResponse)
async def trigger_workflow(request: WorkflowTrigger):
    # Placeholder - will be implemented in FASE 5
    return WorkflowResponse(
        status="success",
        result={"message": "Workflow triggered"}
    )
