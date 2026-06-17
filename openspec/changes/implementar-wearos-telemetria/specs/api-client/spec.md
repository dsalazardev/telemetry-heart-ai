## ADDED Requirements

### Requirement: Send telemetry data via POST /telemetria
The system SHALL send HR data to the backend using `POST /telemetria` with proper authentication.

#### Scenario: Successful telemetry submission
- **WHEN** it is time to submit telemetry data (every 60 seconds, configurable)
- **AND** the device is connected to the network
- **AND** a valid JWT token is available
- **THEN** the system SHALL send a POST request to `/telemetria`
- **AND** the request body SHALL contain `frecuenciaCardiaca`, `spo2` (null if not available), `anomaliaEcg` (null), `timestamp` (ISO8601), `dispositivo_id`
- **AND** the request header SHALL contain `Authorization: Bearer <token>`
- **AND** on HTTP 201, the system SHALL log success

#### Scenario: Telemetry submission fails with 401
- **WHEN** the backend responds with HTTP 401
- **THEN** the OkHttp Authenticator SHALL attempt token refresh
- **AND** if refresh fails, the system SHALL store the telemetry in the offline queue

#### Scenario: Telemetry submission fails with network error
- **WHEN** the network is unavailable or the request times out
- **THEN** the system SHALL store the telemetry payload in the offline queue
- **AND** the system SHALL retry when connectivity returns

### Requirement: Register device via POST /dispositivos
The system SHALL register the WearOS device with the backend on first launch to obtain a JWT.

#### Scenario: First launch registration
- **WHEN** the app launches for the first time (no token in DataStore)
- **THEN** the system SHALL send a POST request to `/dispositivos`
- **AND** the request body SHALL contain `tipo: "WearOS"`, `modelo` (device model), `sistemaOperativo` (OS version), `paciente_id` (configurable)
- **AND** on HTTP 201, the system SHALL store the returned `tokenAutenticacion` in DataStore
- **AND** on HTTP 201, the system SHALL store the `dispositivo_id`

#### Scenario: Registration fails
- **WHEN** POST /dispositivos fails (network error or server error)
- **THEN** the system SHALL retry after 30 seconds
- **AND** the UI SHALL show a "connection failed" indicator
