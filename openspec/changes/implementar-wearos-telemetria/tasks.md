## 1. Dependencies and Configuration

- [x] 1.1 Update `gradle/libs.versions.toml`: add health-services-client, OkHttp 5.4.0, Retrofit 3.0.0, kotlinx-serialization-json 1.9.0, kotlinx-coroutines-android 1.11.0, DataStore Preferences 1.2.1, Room 2.8.4
- [x] 1.2 Update `app/build.gradle.kts`: add KSP plugin for Room, add all new dependencies from libs.versions.toml
- [x] 1.3 Update `app/build.gradle.kts`: add buildConfigField for BACKEND_URL (default "http://10.0.2.2:8000")
- [x] 1.4 Create `app/.env.example` with BACKEND_URL variable documentation
- [x] 1.5 Update `AndroidManifest.xml`: add BODY_SENSORS (maxSdkVersion=35), READ_HEART_RATE, FOREGROUND_SERVICE, FOREGROUND_SERVICE_HEALTH, INTERNET, ACCESS_NETWORK_STATE, RECEIVE_BOOT_COMPLETED permissions
- [x] 1.6 Update `AndroidManifest.xml`: declare TelemetryForegroundService with `android:foregroundServiceType="health"`
- [x] 1.7 Update `AndroidManifest.xml`: add `<uses-feature android:name="android.hardware.sensor.heartrate" android:required="true" />`
- [x] 1.8 Update `strings.xml`: add strings for telemetry UI (hr_label, risk_level, connection_status, etc.)

## 2. Data Layer — Local Storage

- [x] 2.1 Create `data/local/TokenStorage.kt`: DataStore Preferences wrapper for JWT token (save, read, clear, observe via Flow)
- [x] 2.2 Create `data/local/TelemetryDatabase.kt`: Room database class with DAO for offline queue
- [x] 2.3 Create Room entity `OfflineTelemetryEntity` with fields: id, timestamp, payload (JSON string), estado (pendiente/enviado/error), intentos, ultimoIntento
- [x] 2.4 Create `OfflineQueueDao` with queries: insert, queryAllPendiente, updateStatus, count, deleteOldest
- [x] 2.5 Create `data/local/OfflineQueue.kt`: repository wrapping DAO with enqueue(), dequeue(), retry() logic including exponential backoff

## 3. Data Layer — Sensor

- [x] 3.1 Create `data/sensor/HealthSensor.kt`: singleton wrapper for Health Services API with PassiveMonitoringClient setup
- [x] 3.2 Implement `HealthDataHolder` object: StateFlow<HealthData> with HR, timestamp, risk level
- [ ] 3.3 Register `PassiveListenerService` to receive batched HR data points and update HealthDataHolder
- [ ] 3.4 Implement runtime permission request logic branching by API level (API 36+ → HealthPermissions.READ_HEART_RATE, else → BODY_SENSORS)
- [ ] 3.5 Add manual MeasureClient reading for "check now" button on UI

## 4. Data Layer — Remote API

- [x] 4.1 Create `data/remote/BackendApi.kt`: Retrofit interface with POST /dispositivos and POST /telemetria methods
- [x] 4.2 Create `data/remote/AuthInterceptor.kt`: OkHttp Interceptor that injects Bearer token from TokenStorage
- [x] 4.3 Create OkHttp Authenticator implementation: intercept 401, re-register device via POST /dispositivos, update token, retry original request
- [x] 4.4 Create OkHttp client singleton with interceptor, authenticator, and 30s timeouts
- [x] 4.5 Create retrofit instance with okhttp client and kotlinx-serialization converter
- [x] 4.6 Create `TelemetryRepository.kt`: coordinates between BackendApi, OfflineQueue, and TokenStorage, exposes submitTelemetry() with offline fallback

## 5. Services

- [x] 5.1 Create `TelemetryApplication.kt`: Application subclass that initializes HealthServices connection on app start
- [x] 5.2 Create `service/TelemetryForegroundService.kt`: Foreground Service with type "health", notification with HR display
- [x] 5.3 Implement Health Services listener registration inside foreground service (onStartCommand)
- [x] 5.4 Implement periodic telemetry submission inside foreground service (every 60s via coroutine delay)
- [x] 5.5 Create BootReceiver: BroadcastReceiver for ACTION_BOOT_COMPLETED that starts TelemetryForegroundService
- [x] 5.6 Register BootReceiver in AndroidManifest.xml
- [x] 5.7 Implement service lifecycle: start from MainActivity, stop on app close, cleanup listeners

## 6. Presentation Layer

- [x] 6.1 Create `presentation/TelemetryScreen.kt`: Composable showing HR, risk level indicator (color-coded), connection status, last update timestamp
- [x] 6.2 Create `presentation/ConnectionIndicator.kt`: small Composable showing green/yellow/red dot for connection status
- [x] 6.3 Update `presentation/theme/Theme.kt`: add risk-level colors (green, yellow, red), health-data color scheme
- [x] 6.4 Update `MainActivity.kt`: replace placeholder buttons with TelemetryScreen, request permissions on start, start foreground service
- [x] 6.5 Add onboarding/permission-request flow to MainActivity for first launch (BODY_SENSORS or HealthPermissions)
- [x] 6.6 Add manual "Check HR" button to UI that triggers MeasureClient reading

## 7. Tile

- [x] 7.1 Replace `MainTileService.kt` with `HrTileService.kt` using Material3TileService from ProtoLayout 1.4
- [x] 7.2 Implement `tileResponse` suspend function: build timeline with HR and risk indicator from HealthDataHolder
- [x] 7.3 Call `requestRebuild()` from TelemetryForegroundService when new HR data arrives
- [x] 7.4 Update tile resources: preview image, tile label string

## 8. Complication

- [x] 8.1 Replace placeholder `MainComplicationService.kt` with `HrComplicationService.kt`: read HR from HealthDataHolder via onComplicationRequest
- [x] 8.2 Return ShortTextComplicationData with HR value and color-coded risk as content description
- [x] 8.3 Call `notifyComplicationUpdate()` from TelemetryForegroundService when new HR data arrives
- [x] 8.4 Update complication metadata: supported types, update period

## 9. Testing and Verification

- [ ] 9.1 Verify synthetic data: `adb shell am broadcast -a "whs.USE_SYNTHETIC_PROVIDERS" ...` (**manual — needs physical watch**)
- [ ] 9.2 Set up ADB reverse proxy: `adb reverse tcp:8000 tcp:8000` (**manual — needs physical watch**)
- [ ] 9.3 Test device registration flow (**manual — needs physical watch + backend**)
- [ ] 9.4 Test telemetry submission (**manual — needs physical watch + backend**)
- [ ] 9.5 Test offline flow (**manual — needs physical watch**)
- [ ] 9.6 Verify complication renders HR (**manual — needs watch face setup**)
- [ ] 9.7 Verify tile displays HR (**manual — needs tile setup on watch**)
- [ ] 9.8 Test boot receiver (**manual — needs watch restart**)
- [ ] 9.9 Test permission denial flow (**manual**)
