## ADDED Requirements

### Requirement: Agent training endpoint
The system SHALL accept a POST request to `/agent/train` to trigger model retraining with a provided dataset.

#### Scenario: Successful training
- **WHEN** a client sends a POST request to `/agent/train` with a JSON body containing `dataset_path` (string) and optional hyperparameters
- **THEN** the system trains a new RandomForest model using the provided dataset
- **AND** saves the model to `model.pkl`
- **AND** returns HTTP 200 with `accuracy` (float), `f1_score` (float), and `model_path` (string)

#### Scenario: Dataset not found
- **WHEN** a client sends a POST request to `/agent/train` with a non-existent `dataset_path`
- **THEN** the system returns HTTP 404 with an error message "Dataset not found"
