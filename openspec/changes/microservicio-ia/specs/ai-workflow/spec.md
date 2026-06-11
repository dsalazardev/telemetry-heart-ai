## ADDED Requirements

### Requirement: Workflow trigger endpoint
The system SHALL accept a POST request to `/workflow/trigger` to execute an external workflow via an Adapter.

#### Scenario: Successful workflow trigger
- **WHEN** a client sends a POST request to `/workflow/trigger` with `adapter_id` (int) and `payload` (JSON)
- **THEN** the system retrieves the `Adapter` configuration from the database
- **AND** calls the external endpoint (`Adapter.endpoint`) with the payload
- **AND** returns HTTP 200 with the external response

#### Scenario: Adapter not found
- **WHEN** a client sends a POST request to `/workflow/trigger` with a non-existent `adapter_id`
- **THEN** the system returns HTTP 404 with an error message "Adapter not found"

#### Scenario: External service failure
- **WHEN** the external endpoint returns an error or times out
- **THEN** the system returns HTTP 502 with the error details
- **AND** logs the failure for monitoring

### Requirement: Adapter model stores workflow configurations
The system SHALL provide an `Adapter` model to store external workflow configurations.

#### Scenario: Adapter creation
- **WHEN** an `Adapter` record is created with `proveedor`, `endpoint`, `flujo`, and `token`
- **THEN** the system stores the configuration in the `Adapter` table
- **AND** the `flujo` field stores the workflow definition as JSON

#### Scenario: Adapter execution
- **WHEN** `Adapter.ejecutarFlujo()` is called with a payload
- **THEN** the system makes an HTTP POST request to `endpoint` with the payload and `token` in the Authorization header
- **AND** returns the response
