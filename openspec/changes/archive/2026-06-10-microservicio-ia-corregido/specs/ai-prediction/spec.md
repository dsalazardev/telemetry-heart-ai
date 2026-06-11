## ADDED Requirements

### Requirement: Prediction endpoint accepts exact 13 features
The system SHALL accept a POST request to `/predict` with exactly 13 features matching the heart dataset schema and return a cardiac risk prediction with all fields from the `Prediccion` model.

#### Scenario: Successful prediction with exact features
- **WHEN** a client sends a POST request to `/predict` with a JSON body containing the exact 13 features:
  - `age` (int): Edad en años
  - `sex` (int): 1 = masculino, 0 = femenino
  - `cp` (int): Tipo de dolor torácico (0-3)
  - `trestbps` (int): Presión arterial en reposo (mmHg)
  - `chol` (int): Colesterol sérico (mg/dl)
  - `fbs` (bool): Glucosa en ayunas > 120 mg/dl
  - `restecg` (int): Resultados electrocardiográficos (0-2)
  - `thalach` (int): Frecuencia cardíaca máxima alcanzada
  - `exang` (bool): Angina inducida por ejercicio
  - `oldpeak` (float): Depresión ST inducida por ejercicio
  - `slope` (int): Pendiente del segmento ST (0-2)
  - `ca` (int): Número de vasos principales coloreados (0-3)
  - `thal` (int): Talasemia (0-3)
- **THEN** the system returns a JSON response with:
  - `probabilidad` (float): Probabilidad de riesgo (0.0 - 1.0)
  - `clasificacion` (string): "bajo" | "medio" | "alto"
  - `versionModelo` (string): Versión del modelo (ej: "rf-v1.2")
  - `tiempoMs` (float): Tiempo de inferencia en milisegundos
  - `importanciaVariables` (JSON): Dict con `feature_importances_` del modelo
  - `explicacionClinica` (string): "Riesgo {clasificacion}: {probabilidad:.1%}"

#### Scenario: Missing features
- **WHEN** a client sends a POST request to `/predict` with fewer than 13 features or missing any of the exact feature names
- **THEN** the system returns HTTP 422 with an error message indicating missing fields

#### Scenario: Invalid feature types
- **WHEN** a client sends a POST request to `/predict` with `age` as a string instead of int
- **THEN** the system returns HTTP 422 with validation error details

#### Scenario: Model not loaded
- **WHEN** the prediction service is called but the model file (`model.pkl`) is not found
- **THEN** the system returns HTTP 503 with an error message "Model not loaded"
