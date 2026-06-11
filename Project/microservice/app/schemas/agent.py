from typing import Optional
from pydantic import BaseModel

class AgentQuery(BaseModel):
    question: str
    session_id: Optional[str] = None

class AgentResponse(BaseModel):
    response: str
    tool_used: str
    confidence: float

class AgentTrain(BaseModel):
    dataset_path: str
    run_metaheuristics: Optional[bool] = False

class TrainResponse(BaseModel):
    accuracy: float
    f1_score: float
    model_path: str
    features_selected: Optional[int] = None
    best_params: Optional[dict] = None
