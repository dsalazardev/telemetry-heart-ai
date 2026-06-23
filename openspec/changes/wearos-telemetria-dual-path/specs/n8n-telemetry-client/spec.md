## ADDED Requirements

### Requirement: Send telemetry to n8n webhook
The system SHALL send heart rate, simulated SpO2, constant ECG anomaly label, and patient ID to the n8n webhook URL every 60 seconds in parallel with the backend POST. The body SHALL be wrapped in a `body` key as expected by the n8n Function node (`$json.body`).

#### Scenario: Successful n8n telemetry POST
- **WHEN** the 60s telemetry loop fires
- **THEN** the system SHALL POST `{"body": {"paciente_id": <id>, "frecuenciaCardiaca": <hr>, "spo2": <random-90-100>, "anomaliaEcg": "Prueba PoC"}}` to `TELEMETRY_URL`
- **THEN** the system SHALL NOT include any `Authorization` header (no JWT)
- **THEN** the system SHALL log the result at INFO level

#### Scenario: n8n webhook unavailable
- **WHEN** the n8n POST fails with a network error or non-2xx status
- **THEN** the system SHALL log the error at WARN level
- **THEN** the system SHALL NOT retry (fire-and-forget)
- **THEN** the system SHALL NOT block the backend POST

#### Scenario: Simulated SpO2 value
- **WHEN** building the n8n payload
- **THEN** the system SHALL generate SpO2 as `kotlin.random.Random.nextDouble(90.0, 100.0)` rounded to 1 decimal
- **THEN** the system SHALL NOT use null for SpO2 (n8n parseFloat rejects NaN)

#### Scenario: ECG anomaly constant
- **WHEN** building the n8n payload
- **THEN** the system SHALL set `anomaliaEcg` to the string `"Prueba PoC"`
- **THEN** the system SHALL NOT set it to null or empty (n8n sanitization converts empty/null to SQL NULL)

#### Scenario: Configuration via .env
- **WHEN** the app starts
- **THEN** the n8n webhook URL SHALL be read from `BuildConfig.TELEMETRY_URL` (generated from `.env`)
- **THEN** the system SHALL also read `BuildConfig.BACKEND_URL` for the backend path (separate destination)
