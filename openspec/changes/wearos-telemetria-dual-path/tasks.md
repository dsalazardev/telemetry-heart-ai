## 1. Configuration

- [ ] 1.1 Update `.env`: set `BACKEND_URL=http://10.0.2.2:8081` (emulator) or user's local IP, keep `TELEMETRY_URL` as-is
- [ ] 1.2 Update `.env.example` to document both `BACKEND_URL` and `TELEMETRY_URL` with comments

## 2. N8n API Layer

- [ ] 2.1 Create `N8nApi.kt` with `N8nBody`, `N8nPayload` DTOs and `N8nApi` Retrofit interface (`@POST("webhook-test/telemetria")`)
- [ ] 2.2 Add `createN8nClient()` and `createN8nRetrofit()` factory methods to `HttpClient.kt` (no auth, plain OkHttpClient + logging)

## 3. Repository

- [ ] 3.1 Add `sendToN8n(pacienteId, hr, ecg)` method to `TelemetryRepository` generating random SpO2 (90.0-100.0) and POSTing via N8nApi

## 4. Service Wiring

- [ ] 4.1 Wire `N8nApi` singleton in `TelemetryApplication.onCreate()` using `BuildConfig.TELEMETRY_URL`
- [ ] 4.2 In `TelemetryForegroundService.startTelemetryLoop()`, after backend POST, call `telemetryRepository.sendToN8n()` with `pacienteId` from TokenStorage and `anomaliaEcg = "Prueba PoC"`

## 5. Verify

- [x] 5.1 `./gradlew assembleDebug` — BUILD SUCCESSFUL
- [ ] 5.2 Observe logcat for `Telemetry sent: fc=XX` (backend) and n8n POST log lines (**manual** — requires running on watch)
