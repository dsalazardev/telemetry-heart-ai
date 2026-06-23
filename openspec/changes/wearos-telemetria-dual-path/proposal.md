## Why

WearOS currently sends telemetry only to the backend FastAPI (`POST /telemetria`), but the n8n webhook workflow that triggers microservice risk evaluation (`POST /predecir`) never receives data because:
1. Backend does not forward to n8n
2. `BACKEND_URL` in `.env` is misconfigured pointing to n8n instead of the backend
3. `TELEMETRY_URL` exists in `.env` but is never referenced in code
4. `TelemetryRequest` body doesn't match what n8n expects (missing `paciente_id`, wrong wrapper format)

## What Changes

- Fix `BACKEND_URL` in `.env` to point to backend FastAPI (`http://10.0.2.2:8081` for emulator)
- Wire up `TELEMETRY_URL` from `.env` for n8n webhook
- Create `N8nApi` Retrofit interface with `N8nPayload`/`N8nBody` DTOs wrapping data in `body` key
- Add n8n OkHttpClient factory (no auth interceptors) and Retrofit to `HttpClient.kt`
- Add `sendToN8n()` method to `TelemetryRepository` generating random SpO2 (90-100 range)
- Modify telemetry loop in `TelemetryForegroundService` to POST to both backend and n8n every 60s
- Wire `N8nApi` singleton in `TelemetryApplication`

## Capabilities

### New Capabilities
- `n8n-telemetry-client`: Sending heart rate, simulated SpO2, constant ECG anomaly, and patient ID to n8n webhook via Retrofit, wrapping payload in `body` key as n8n expects

### Modified Capabilities
- *(none)*

## Impact

- **WearOS (6 files)**: `.env`, new `N8nApi.kt`, `HttpClient.kt`, `TelemetryRepository.kt`, `TelemetryForegroundService.kt`, `TelemetryApplication.kt`
- **Backend**: No changes
- **n8n**: No changes — the webhook workflow already expects this exact format
- **Dependencies**: No new Gradle dependencies needed
