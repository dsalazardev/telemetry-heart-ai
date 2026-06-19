from fastapi import APIRouter, HTTPException
from app.schemas.agent import AgentQuery, AgentResponse, AgentTrain, TrainResponse
from app.services.langchain_agent_service import AgentService

router = APIRouter()
agent_service = AgentService()

@router.post("/query", response_model=AgentResponse)
async def agent_query(request: AgentQuery):
    if not request.question:
        raise HTTPException(status_code=400, detail="Question is required")
    
    result = agent_service.query(
        request.question,
        session_id=request.session_id or "default"
    )
    
    return AgentResponse(**result)

@router.post("/train", response_model=TrainResponse)
async def agent_train(request: AgentTrain):
    # Placeholder for training endpoint
    return TrainResponse(
        accuracy=0.0,
        f1_score=0.0,
        model_path="placeholder"
    )
