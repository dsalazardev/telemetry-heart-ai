from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.predict import EvaluarRequest, EvaluarResponse
from app.models.lectura import Lectura
from app.models.prediccion import Prediccion
from app.models.evaluacion import Evaluacion
from app.services.predictor_service import PredictorService

router = APIRouter()
predictor = PredictorService()

@router.post("/", response_model=EvaluarResponse)
async def evaluar(request: EvaluarRequest, db: AsyncSession = Depends(get_db)):
    try:
        # Create lectura
        lectura = Lectura(
            age=request.lectura.age,
            sex=request.lectura.sex,
            cp=request.lectura.cp,
            trestbps=request.lectura.trestbps,
            chol=request.lectura.chol,
            fbs=request.lectura.fbs,
            restecg=request.lectura.restecg,
            thalach=request.lectura.thalach,
            exang=request.lectura.exang,
            oldpeak=request.lectura.oldpeak,
            slope=request.lectura.slope,
            ca=request.lectura.ca,
            thal=request.lectura.thal
        )
        db.add(lectura)
        await db.flush()
        
        # Predict
        features = lectura.exportarVector()
        result = predictor.predict(features)
        
        # Create prediccion
        prediccion = Prediccion(
            versionModelo=result["versionModelo"],
            probabilidad=result["probabilidad"],
            clasificacion=result["clasificacion"],
            tiempoMs=result["tiempoMs"],
            importanciaVariables=result["importanciaVariables"]
        )
        db.add(prediccion)
        await db.flush()
        
        # Create evaluacion
        evaluacion = Evaluacion(
            origenDatos=request.origenDatos,
            paciente_id=request.paciente_id,
            lectura_id=lectura.id,
            prediccion_id=prediccion.id
        )
        db.add(evaluacion)
        await db.commit()
        
        return EvaluarResponse(
            id=evaluacion.id,
            fechaEvaluacion=evaluacion.fechaEvaluacion,
            origenDatos=evaluacion.origenDatos,
            paciente_id=evaluacion.paciente_id,
            lectura_id=evaluacion.lectura_id,
            prediccion_id=evaluacion.prediccion_id,
            clasificacion=prediccion.clasificacion,
            probabilidad=prediccion.probabilidad
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
