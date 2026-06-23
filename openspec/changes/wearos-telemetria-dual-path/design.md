## Context

Current WearOS telemetry pipeline:

```
WearOS ──POST /telemetria──▶ Backend :8000 (registro + JWT + envío)
```

Problems discovered:
1. `BACKEND_URL` in `.env` points to n8n webhook URL instead of backend, causing doubled path (`/telemetria/telemetria`)
2. `TelemetryRequest` uses `dispositivo_id` but n8n expects `paciente_id` wrapped in `body` key
3. Backend does not forward to n8n, so the microservice risk evaluation (RandomForest via `POST /predecir`) never fires

The `.env` already defines `TELEMETRY_URL` pointing to the n8n webhook, but it's never referenced in code.

## Goals / Non-Goals

**Goals:**
- WearOS sends telemetry to both backend FastAPI AND n8n webhook every 60s
- Backend receives `dispositivo_id` + JWT (existing flow, unchanged)
- n8n receives `paciente_id`, `frecuenciaCardiaca`, simulated SpO2, constant ECG label
- Zero changes to backend or n8n code
- No new Gradle dependencies

**Non-Goals:**
- Real SpO2 sensor data (simulated with random)
- Real ECG anomaly detection (constant string "Prueba PoC")
- Offline queue for n8n path (only backend has offline queue)
- Backend forwarding to n8n (that's an architectural change for later)

## Decisions

### 1. Dual-path vs Backend-forwarding
- **Approach**: WearOS sends to BOTH destinations in parallel
- **Rationale**: Zero backend changes. n8n already expects the exact body format. WearOS already has the 60s loop and the paciente_id stored from registration.
- **Alternatives considered**: Backend forwarding to n8n (requires backend HTTP client + env config + changes to FastAPI routes)

### 2. n8n body wrapper (`body` key)
- **Approach**: Retrofit serializes `N8nPayload(N8nBody(...))` producing `{"body": {"paciente_id": ..., ...}}`
- **Rationale**: The n8n Function node accesses `$json.body`, so the POST must wrap data under a `body` key
- **Alternatives considered**: Raw OkHttp POST with manual JSON serialization (more boilerplate)

### 3. Separate Retrofit instance for n8n
- **Approach**: New `N8nApi` Retrofit interface + new OkHttpClient without auth interceptors
- **Rationale**: n8n requires no JWT auth. Backend Retrofit has `AuthInterceptor` + `AuthAuthenticator`. Reusing it would send Bearer tokens to n8n unnecessarily.
- **Alternatives considered**: Single Retrofit with conditional auth (couples concerns)

### 4. Simulated SpO2
- **Approach**: `kotlin.random.Random.nextDouble(90.0, 100.0)` rounded to 1 decimal
- **Rationale**: n8n's sanitization (`parseFloat`) rejects NaN. Real SpO2 sensors not available on current hardware.
- **Range**: 90.0-100.0 represents normal clinical SpO2 range

### 5. ECG anomaly constant
- **Approach**: String constant `"Prueba PoC"` passed as `anomaliaEcg`
- **Rationale**: No actual ECG sensor. n8n sanitization accepts non-empty string (single-escaped for SQL).

### 6. No offline queue for n8n
- **Approach**: Fire-and-forget HTTP POST to n8n, no retry logic
- **Rationale**: PoC phase. Backend already handles offline queue for core data persistence.

## Risks / Trade-offs

- **Risks: n8n webhook unavailable** → WearOS will log the error but the microservice risk evaluation won't fire for that cycle. Mitigation: The backend path still persists telemetry, so no data loss.
- **Risks: Simulated SpO2 masks real issues** → For production, replace with real sensor data. Mitigation: This is clearly a PoC-only feature.
- **Risks: Double POST on each cycle** → Two HTTP calls every 60s is negligible on WiFi. Mitigation: If battery becomes a concern, batch or reduce n8n frequency.
