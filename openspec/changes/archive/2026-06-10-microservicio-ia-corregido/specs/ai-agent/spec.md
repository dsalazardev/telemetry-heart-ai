## ADDED Requirements

### Requirement: Agent training endpoint
The system SHALL accept a POST request to `/agent/train` to trigger model retraining with a provided dataset and optional metaheuristics.

#### Scenario: Successful training
- **WHEN** a client sends a POST request to `/agent/train` with a JSON body containing:
  - `dataset_path` (string): Ruta al dataset CSV
  - `run_metaheuristics` (bool, optional): Ejecutar AG + PSO
- **THEN** the system trains a new RandomForest model using the provided dataset
- **AND** saves the model to `model.pkl`
- **AND** returns HTTP 200 with:
  - `accuracy` (float): Accuracy del modelo
  - `f1_score` (float): F1-score weighted
  - `model_path` (string): Ruta al modelo guardado

#### Scenario: Training with metaheuristics
- **WHEN** `run_metaheuristics` is true
- **THEN** the system first runs DEAP AG (50 ind × 20 gen) for feature selection
- **AND** then runs custom PSO (30 part × 30 iter) for hyperparameter tuning
- **AND** stores AG results in `Prediccion.importanciaVariables` (JSON)
- **AND** stores PSO results in `Prediccion.metadataTecnica` (JSON)

#### Scenario: Dataset not found
- **WHEN** a client sends a POST request to `/agent/train` with a non-existent `dataset_path`
- **THEN** the system returns HTTP 404 with an error message "Dataset not found"
