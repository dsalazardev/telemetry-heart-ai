from fastapi import APIRouter
from datetime import datetime
from app.core.settings import settings
from app.services.predictor_service import PredictorService
import os

router = APIRouter()
predictor = PredictorService()

@router.get("/")
async def health():
    # Check database
    db_status = "ok"  # Simplified for now
    
    # Check model
    model_status = "ok" if predictor.is_ready() else "error"
    
    # Check chroma
    chroma_path = settings.CHROMA_PATH
    chroma_status = "ok" if os.path.exists(chroma_path) else "error"
    
    overall = "ok" if all(s == "ok" for s in [db_status, model_status, chroma_status]) else "error"
    
    return {
        "status": overall,
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {
            "database": db_status,
            "model": model_status,
            "chroma": chroma_status
        }
    }
