from fastapi import APIRouter, HTTPException
from app.schemas.predict import PredictRequest, PredictResponse
from app.services.predictor_service import PredictorService

router = APIRouter()
predictor = PredictorService()

@router.post("", response_model=PredictResponse)
async def predict(request: PredictRequest):
    if not predictor.is_ready():
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        features = [
            request.age, request.sex, request.cp, request.trestbps,
            request.chol, request.fbs, request.restecg, request.thalach,
            request.exang, request.oldpeak, request.slope, request.ca, request.thal
        ]
        result = predictor.predict(features)
        return PredictResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
