## ADDED Requirements

### Requirement: Evaluation endpoint creates triage records
The system SHALL accept a POST request to `/evaluar` with a payload matching the n8n webhook format and persist the evaluation results in the database.

#### Scenario: Successful evaluation
- **WHEN** a client sends a POST request to `/evaluar` with a JSON payload containing `lectura` (patient data), `prediccion` (features), and `dispositivo_id` (optional)
- **THEN** the system creates a `Lectura` record, a `Prediccion` record, and an `Evaluacion` record linked to both
- **AND** the system returns HTTP 201 with the created `Evaluacion` object including `score` and `nivel_riesgo`

#### Scenario: Invalid payload
- **WHEN** a client sends a POST request to `/evaluar` with a malformed payload
- **THEN** the system returns HTTP 422 with validation error details

#### Scenario: Workflow trigger
- **WHEN** the evaluation is complete and a `workflow_id` is provided
- **THEN** the system calls the corresponding `Adapter` to execute the workflow
