import os
import time
import joblib
import numpy as np
from typing import List, Dict, Optional
from app.core.settings import settings

class PredictorService:
    def __init__(self):
        self.model = None
        self.model_path = settings.MODEL_PATH
        self.version = "rf-v1.0"
        self.load_model()
    
    def load_model(self):
        """Load model from disk"""
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            print(f"[OK] Model loaded: {self.model_path}")
        else:
            print(f"[WARN] Model not found at {self.model_path}")
    
    def predict(self, features: List[float]) -> Dict:
        """Predict cardiac risk from 13 features"""
        if self.model is None:
            raise ValueError("Model not loaded")
        
        start = time.time()
        X = np.array(features).reshape(1, -1)
        
        # Predict class
        prediction = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0]
        
        # Map to classification
        clasificacion = self._map_class(prediction)
        probabilidad = float(max(probabilities))
        
        elapsed = (time.time() - start) * 1000
        
        # Feature importance
        importancia = self.get_feature_importance()
        
        return {
            "probabilidad": probabilidad,
            "clasificacion": clasificacion,
            "versionModelo": self.version,
            "tiempoMs": elapsed,
            "importanciaVariables": importancia,
            "explicacionClinica": f"Riesgo {clasificacion}: {probabilidad:.1%}"
        }
    
    def _map_class(self, prediction: int) -> str:
        mapping = {0: "bajo", 1: "medio", 2: "alto"}
        return mapping.get(prediction, "desconocido")
    
    def get_feature_importance(self) -> Optional[Dict]:
        if self.model is None:
            return None
        
        features = [
            "age", "sex", "cp", "trestbps", "chol", "fbs",
            "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal"
        ]
        
        importances = self.model.feature_importances_
        return {f: float(v) for f, v in zip(features, importances)}
    
    def is_ready(self) -> bool:
        return self.model is not None
