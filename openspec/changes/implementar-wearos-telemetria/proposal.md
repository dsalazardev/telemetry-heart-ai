## Why

The WearOS module is a 100% skeleton (~238 placeholder lines, 4 `.kt` files) with no real sensor data, no HTTP communication, no foreground service, and no live UI. A Samsung Galaxy Watch 4 (SM-R860, API 36) is connected and ready for debugging, but the app cannot collect or transmit health telemetry. This change implements the full data pipeline: heart rate sensor → foreground service → HTTP POST to backend, with offline fallback, complications, and tiles.

## What Changes

- **Health Services integration**: PassiveMonitoringClient reads HR in background, MeasureClient for real-time
- **Foreground Service**: Continuous HR collection with mandatory notification (type "health")
- **Backend HTTP communication**: OkHttp 5.4.0 + Retrofit 3.0.0 with kotlinx-serialization
- **JWT authentication**: Device registration via POST /dispositivos, token persisted in DataStore
- **Offline queue**: Room DB stores failed telemetry payloads with retry backoff
- **UI**: Live HR display, connection indicator, risk level (bajo/medio/alto)
- **Complication**: HR + color-coded risk on watch face
- **Tile**: HR + status via Material3TileService
- **Dependency updates**: `libs.versions.toml` (add OkHttp, Retrofit, Room, DataStore, kotlinx-serialization, Tiles, ProtoLayout, Health Services)
- **Permissions**: BODY_SENSORS(maxSdkVersion=35), READ_HEART_RATE, FOREGROUND_SERVICE_HEALTH, INTERNET, RECEIVE_BOOT_COMPLETED
- **SPO2 and ECG**: Identified as out of scope for this iteration (SPO2 requires separate Health Connect API; ECG has no standard anomaly API)

## Capabilities

### New Capabilities
- `sensor-hr`: Heart rate data collection via Health Services API (PassiveMonitoringClient + MeasureClient)
- `foreground-service`: Background health data collection with notification and boot receiver
- `api-client`: Backend HTTP communication with Retrofit + OkHttp (POST /dispositivos, POST /telemetria)
- `token-auth`: Device JWT authentication with DataStore persistence and automatic refresh via OkHttp Authenticator
- `offline-queue`: Room-based offline telemetry storage with retry backoff
- `tile-hr`: Wear OS Tile displaying heart rate + connection status via Material3TileService
- `complication-hr`: Watch face complication showing HR + color-coded risk level

### Modified Capabilities
- (none)

## Impact

- **All files in `Project/wearos/app/src/main/java/com/example/wearos/`**: rewritten from placeholders to real implementations
- **`Project/wearos/gradle/libs.versions.toml`**: add dependencies for Health Services, OkHttp, Retrofit, Room, DataStore, kotlinx-serialization, Tiles, ProtoLayout, Horologist
- **`Project/wearos/app/build.gradle.kts`**: add new dependencies, KSP plugin for Room
- **`Project/wearos/app/src/main/AndroidManifest.xml`**: add all required permissions and service declarations
- **Backend**: Device registration flow must be implemented (POST /dispositivos endpoint exists, needs WearOS client)
- **ADB**: `adb reverse tcp:8000 tcp:8000` required to connect watch to local backend
