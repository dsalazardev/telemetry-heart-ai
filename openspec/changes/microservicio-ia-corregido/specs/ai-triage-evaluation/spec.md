## ADDED Requirements

### Requirement: Evaluation endpoint creates triage records with exact UML model
The system SHALL accept a POST request to `/evaluar` with a payload matching the n8n webhook format and persist the evaluation results in the database using the exact `Evaluacion` model attributes.

#### Scenario: Successful evaluation with exact model
- **WHEN** a client sends a POST request to `/evaluar` with a JSON payload containing:
  - `lectura` (object): 13 features + `target` (optional)
  - `dispositivo_id` (int, optional): ID del dispositivo
  - `workflow_id` (int, optional): ID del Adapter a ejecutar
- **THEN** the system creates a `Lectura` record with the exact 13 features and `fechaCreacion`
- **AND** creates a `Prediccion` record with `versionModelo`, `probabilidad`, `clasificacion`, `tiempoMs`, `fecha`, `importanciaVariables` (JSON), `metadataTecnica` (JSON)
- **AND** creates an `Evaluacion` record with:
  - `fechaEvaluacion` (datetime, auto)
  - `origenDatos` (string): "telemetria" | "manual" | "batch"
  - `paciente_id` (int): FK → `pacientes.id` (backend, cross-module)
  - `lectura_id` (int): FK → `lecturas.id`
  - `prediccion_id` (int): FK → `predicciones.id`
- **AND** the system returns HTTP 201 with the created `Evaluacion` object

#### Scenario: Invalid payload
- **WHEN** a client sends a POST request to `/evaluar` with a malformed payload
- **THEN** the system returns HTTP 422 with validation error details

#### Scenario: Workflow trigger
- **WHEN** the evaluation is complete and a `workflow_id` is provided
- **THEN** the system retrieves the `Adapter` from `adapters` table
- **AND** calls `Adapter.ejecutarFlujo()` with the evaluation payload
