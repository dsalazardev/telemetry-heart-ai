## ADDED Requirements

### Requirement: Health check endpoint
The system SHALL provide a GET endpoint `/health` that returns the service status.

#### Scenario: Healthy service
- **WHEN** a client sends a GET request to `/health`
- **THEN** the system returns HTTP 200 with a JSON body containing `status: "ok"`, `version` (string), and `timestamp` (ISO 8601)

#### Scenario: Unhealthy service
- **WHEN** the database connection is unavailable
- **THEN** the system returns HTTP 503 with `status: "error"` and `detail` describing the failure

### Requirement: Service startup health
The system SHALL verify all critical dependencies on startup.

#### Scenario: Startup check
- **WHEN** the microservice starts
- **THEN** it checks the database connection
- **AND** it checks if the model file (`model.pkl`) exists
- **AND** it checks if the ChromaDB collection is accessible
- **AND** logs the status of each dependency
