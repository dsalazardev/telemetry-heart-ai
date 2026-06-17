## ADDED Requirements

### Requirement: Store JWT token in DataStore
The system SHALL persist the JWT authentication token using DataStore Preferences.

#### Scenario: Token is saved after device registration
- **WHEN** the device successfully registers via POST /dispositivos
- **THEN** the system SHALL store `tokenAutenticacion` in DataStore
- **AND** the token SHALL persist across app restarts

#### Scenario: Token is loaded on app start
- **WHEN** the application starts
- **THEN** the system SHALL read the JWT token from DataStore
- **AND** if present, use it for all authenticated requests
- **AND** if absent, trigger device registration

### Requirement: Add Bearer token to requests via OkHttp Interceptor
The system SHALL add the JWT token to every API request using an OkHttp `Interceptor`.

#### Scenario: Outgoing request has Bearer token
- **WHEN** any API request is made via Retrofit
- **THEN** the interceptor SHALL add `Authorization: Bearer <token>` header
- **AND** if no token is available, the request SHALL proceed without auth header

### Requirement: Auto-refresh token on 401 via OkHttp Authenticator
The system SHALL automatically re-register the device when the backend returns HTTP 401.

#### Scenario: Token expired and refresh succeeds
- **WHEN** the backend responds with HTTP 401 to any request
- **THEN** the OkHttp Authenticator SHALL intercept the response
- **AND** attempt to re-register via POST /dispositivos
- **AND** on success, update the token in DataStore
- **AND** retry the original request with the new token

#### Scenario: Token refresh fails
- **WHEN** re-registration (POST /dispositivos) also fails
- **THEN** the system SHALL not retry the original request
- **AND** the UI SHALL show "authentication error"
- **AND** the system SHALL queue any pending telemetry for retry later
