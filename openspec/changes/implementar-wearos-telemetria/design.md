## Context

The WearOS module (`Project/wearos/`) is a 100% skeleton — 4 `.kt` files totaling ~238 lines, all placeholder. No sensors, no HTTP client, no foreground service, no live UI. A Samsung Galaxy Watch 4 (SM-R860, API 36) is connected via WiFi ADB and ready for debugging.

The backend exposes:
- **POST /dispositivos** — device registration (no auth), returns JWT
- **POST /telemetria** — telemetry submission (Bearer JWT auth), validates HR 30-220, SPO2 0-100
- **WebSocket /ws/telemetria/{id}** — real-time broadcast (WearOS does NOT need to implement this)

The stack uses Kotlin 2.2.10, AGP 9.2.1, compileSdk 36, targetSdk 36, minSdk 30. Current `libs.versions.toml` lacks Health Services client, OkHttp, Retrofit, Room, DataStore, kotlinx-serialization, and Horologist.

Technical findings verified with ctx7 this session:
- Health Services API split at API 36: `BODY_SENSORS(maxSdkVersion=35)` + `android.permission.health.READ_HEART_RATE`
- PassiveMonitoringClient for background HR, MeasureClient for real-time
- OkHttp 5.4.0 (with coroutines, Authenticator), Retrofit 3.0.0 (with converter-kotlinx-serialization)
- DataStore 1.2.1 for tokens, Room 2.8.4 for offline queue
- Tiles 1.6.0 + ProtoLayout 1.4.0 with Material3TileService
- Complications KTX 1.3.0 with SuspendingComplicationDataSourceService
- Horologist 0.7.15 (stable branch)
- kotlinx-coroutines 1.11.0, kotlinx-serialization 1.9.0

## Goals / Non-Goals

**Goals:**
- Real-time heart rate collection from Health Services (PassiveMonitoringClient)
- Foreground Service collecting HR continuously with "health" type notification
- Device registration via POST /dispositivos on first launch
- Periodic telemetry submission via POST /telemetria with Bearer JWT
- Offline queue (Room) for failed submissions with retry backoff
- Live UI showing HR, connection status, risk level (bajo/medio/alto based on umbrales.json)
- Complication displaying HR + color-coded risk on watch face
- Tile displaying HR + status via Material3TileService
- Token persistence in DataStore across app restarts
- Automatic token refresh via OkHttp Authenticator (re-register device on 401)

**Non-Goals:**
- SPO2 collection (requires separate Health Connect API — out of scope)
- ECG anomaly detection (no standard API, requires custom hardware/ML)
- WebSocket client implementation (broadcasts from backend, not consumed by WearOS)
- n8n integration (they share the same PostgreSQL table via different paths)
- UI customization beyond basic theme colors (risk-indicator colors)
- Multi-watch or multi-user scenarios (single device per patient)

## Decisions

### 1. Health Services API: PassiveMonitoringClient over MeasureClient as primary
- **Decision**: Use PassiveMonitoringClient for continuous background HR collection, with MeasureClient optionally for manual "check now" action.
- **Rationale**: PassiveMonitoringClient provides batched background HR data needed for periodic telemetry. MeasureClient gives single readings on demand but requires the app to be actively requesting. The foreground service provides the necessary execution context for passive monitoring.
- **Alternatives considered**: MeasureClient-only (would miss data when app is not actively reading), manual polling (wasteful).

### 2. HTTP client: OkHttp 5.4.0 + Retrofit 3.0.0 + kotlinx-serialization
- **Decision**: OkHttp with coroutines support for the low-level client, Retrofit for type-safe API interface, kotlinx-serialization for JSON.
- **Rationale**: OkHttp's Authenticator interface enables clean token refresh on 401. Retrofit's converter-kotlinx-serialization provides compile-time safety. kotlinx-serialization is Kotlin-native (no reflection). The `okhttp-coroutines` artifact (`implementation("com.squareup.okhttp3:okhttp-coroutines:5.4.0")`) provides `executeAsync()` extension.
- **Alternatives considered**: Ktor client (different dependency family, less ecosystem integration), plain OkHttp without Retrofit (more boilerplate for serialization).

### 3. Token storage: DataStore Preferences over EncryptedSharedPreferences
- **Decision**: DataStore Preferences 1.2.1 for JWT token storage. Upgrade to EncryptedDataStore if production security is required.
- **Rationale**: DataStore is the modern, coroutine-friendly replacement for SharedPreferences. The token is a simple string — no relational structure needed. For an academic project, DataStore provides adequate security (stored in app-private directory).
- **Alternatives considered**: EncryptedSharedPreferences (adds AndroidX Security dependency), Room for single value (overkill).

### 4. Offline queue: Room over file-based JSON
- **Decision**: Room 2.8.4 with KSP for offline telemetry queue.
- **Rationale**: Room provides structured queries (query by status=pendiente, retry count, timestamp), type-safe DAOs, and coroutine integration. The queue needs to support: insert pending telemetry, query all pending, update status to sent/error, delete old entries. Room handles this cleanly.
- **Alternatives considered**: Plain file I/O with kotlinx-serialization (no query capability, race conditions), DataStore for list (not designed for dynamic collections).

### 5. Tile implementation: Material3TileService over base TileService
- **Decision**: Use ProtoLayout 1.4.0's `Material3TileService` (single suspend `tileResponse` function) instead of the legacy `onTileRequest` + Futures pattern.
- **Rationale**: `Material3TileService` provides a Kotlin-friendly suspend API, auto-manages MaterialScope and ProtoLayoutScope, and simplifies resource handling. It's the recommended path for ProtoLayout 1.4+.
- **Alternatives considered**: Base `TileService` with `onTileRequest` returning `ListenableFuture` (more boilerplate, Guava dependency, less idiomatic Kotlin).

### 6. Complication: SuspendingComplicationDataSourceService (already in use)
- **Decision**: Keep the existing `SuspendingComplicationDataSourceService` pattern, replace placeholder day-of-week data with real HR data from a shared singleton.
- **Rationale**: The existing code already uses the correct coroutine-based class. No architectural change needed — just wire in real data.
- **Alternatives considered**: N/A (already the correct pattern).

### 7. UI architecture: Singleton data holder rather than ViewModel injection
- **Decision**: The Foreground Service writes HR data to a singleton `HealthDataHolder` (object with StateFlow). The Activity, Complication, and Tile read from this singleton.
- **Rationale**: Complications and Tiles are services managed by the system (not Activity-scoped). They cannot easily access Activity ViewModels. A singleton with `StateFlow` provides a simple, lifecycle-safe way to share the latest HR reading across all surfaces.
- **Alternatives considered**: DataStore as shared communication channel (latency), Intent broadcasts (fragile), bound service (over-engineered for a single data point).

### 8. Risk level calculation: Client-side threshold evaluation
- **Decision**: Calculate risk level (bajo/medio/alto) directly on the watch using the threshold values from `umbrales.json`.
- **Rationale**: The backend evaluates risk for the full clinical pipeline (n8n → microservice → RandomForest), but that has latency. The watch needs instant UI feedback. Thresholds are simple: HR < 40 or > 120 = alto, HR < 60 or > 100 = medio, else bajo.
- **Alternatives considered**: Waiting for backend evaluation (latency, requires connectivity), sending to microservice (overkill for simple thresholds).

### 9. Dependency management: ctx7-verified versions in libs.versions.toml
- **Decision**: All new dependency versions are verified with ctx7 before committing to libs.versions.toml.
- **Rationale**: Kotlin/Wear OS ecosystem evolves rapidly. The AGENTS.md mandates ctx7 as source of truth. Versions determined this session: OkHttp 5.4.0, Retrofit 3.0.0, Room 2.8.4, DataStore 1.2.1, kotlinx-serialization 1.9.0, kotlinx-coroutines 1.11.0, Tiles 1.6.0, ProtoLayout 1.4.0, Complications KTX 1.3.0, Horologist 0.7.15, health-services-client (pending ctx7 confirmation).
- **Alternatives considered**: Using previously known versions (risk of outdated deps).

## Risks / Trade-offs

- **[Health Services API 36 migration]** → BODY_SENSORS with maxSdkVersion=35 combined with Health Connect permissions is a relatively new pattern. If the Galaxy Watch 4 doesn't support Health Connect, fall back to BODY_SENSORS only. *Mitigation: Test on the physical device first; implement runtime permission branching based on SDK_INT.*
- **[Wear OS emulator sensor simulation]** → The emulator does not simulate real HR sensors. *Mitigation: Use synthetic data provider (`adb shell am broadcast -a "whs.USE_SYNTHETIC_PROVIDERS"`); physical device (SM-R860) is already connected.*
- **[Backend unavailable during development]** → WearOS cannot reach local backend without ADB reverse proxy. *Mitigation: `adb reverse tcp:8000 tcp:8000` to tunnel; document as setup step.*
- **[Complication update frequency]** → System controls when complications update. Real-time HR display on watch face may have noticeable lag. *Mitigation: Acceptable for academic project; complication updates on each new HR reading via `ComplicationDataSourceService.notifyComplicationUpdate()`.*
- **[Token expiration vs device persistence]** → JWT expires in 30 days. If the device is offline longer than that, token cannot be refreshed from cache. *Mitigation: Authenticator will detect 401, re-register device via POST /dispositivos to get a fresh token.*
- **[Offline queue growth]** → If the watch is offline for extended periods, the Room queue could grow unbounded. *Mitigation: Max 1000 entries; oldest entries evicted. Configurable limit.*
- **[Foreground Service battery drain]** → Continuous HR collection + periodic HTTP POST + notification updates impact battery life. *Mitigation: HR collection at 5-second intervals during active monitoring; configurable interval; service pauses when app is not worn (HR sensor detects no contact).*
