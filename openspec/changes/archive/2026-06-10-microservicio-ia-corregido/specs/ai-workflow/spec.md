## ADDED Requirements

### Requirement: Workflow trigger endpoint
The system SHALL accept a POST request to `/workflow/trigger` to execute an external workflow via an Adapter implementing the `Workflow` interface.

#### Scenario: Successful workflow trigger
- **WHEN** a client sends a POST request to `/workflow/trigger` with:
  - `adapter_id` (int): ID del Adapter
  - `payload` (JSON): Datos a enviar
- **THEN** the system retrieves the `Adapter` from `adapters` table
- **AND** calls `Adapter.ejecutarFlujo(triggerTipo, payload)`
- **AND** returns HTTP 200 with the external response

#### Scenario: Adapter not found
- **WHEN** a client sends a POST request to `/workflow/trigger` with a non-existent `adapter_id`
- **THEN** the system returns HTTP 404 with an error message "Adapter not found"

#### Scenario: External service failure
- **WHEN** the external endpoint returns an error or times out
- **THEN** the system returns HTTP 502 with the error details
- **AND** logs the failure for monitoring

### Requirement: Adapter model stores workflow configurations
The system SHALL provide an `Adapter` model to store external workflow configurations with exact UML attributes.

#### Scenario: Adapter creation
- **WHEN** an `Adapter` record is created with:
  - `proveedor` (str): "n8n" | "langchain" | "manual"
  - `endpoint` (str): URL del webhook
  - `flujo` (JSON): Configuración del workflow
  - `token` (str): Auth token
  - `activo` (bool): Estado
  - `fechaCreacion` (datetime): Timestamp
- **THEN** the system stores the configuration in the `adapters` table

#### Scenario: Adapter execution
- **WHEN** `Adapter.ejecutarFlujo(triggerTipo, payload)` is called
- **THEN** the system makes an HTTP POST request to `endpoint` with the payload and `token` in the Authorization header
- **AND** returns the response

#### Scenario: Urgency notification
- **WHEN** `Adapter.notificarUrgencia(medico_id, mensaje)` is called
- **THEN** the system sends a notification to the configured channel (Telegram, email, etc.)
- **AND** returns `true` if successful
