## ADDED Requirements

### Requirement: Prediction endpoint accepts 13 features
The system SHALL accept a POST request to `/predict` with exactly 13 numerical features in the request body and return a cardiac risk prediction.

#### Scenario: Successful prediction
- **WHEN** a client sends a POST request to `/predict` with a JSON body containing 13 feature values
- **THEN** the system returns a JSON response with `prediction` (0-2), `probability` (array of 3 floats), and `risk_level` (string: "Bajo", "Moderado", "Alto")

#### Scenario: Missing features
- **WHEN** a client sends a POST request to `/predict` with fewer than 13 features
- **THEN** the system returns HTTP 422 with an error message indicating missing fields

#### Scenario: Model not loaded
- **WHEN** the prediction service is called but the model file (`model.pkl`) is not found
- **THEN** the system returns HTTP 503 with an error message "Model not loaded"
