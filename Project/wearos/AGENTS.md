# AGENTS.md — Wear OS

**One-Liner:** Capa de adquisición de telemetría IoT para captura, procesamiento y transmisión de señales biométricas desde dispositivos vestibles hacia la API central del ecosistema Telemetry Heart AI.

**Estado actual: SKELETON / PLACEHOLDER** — El módulo tiene estructura compilable pero cero lógica funcional. Sin sensores, sin HTTP, sin foreground service, sin datos reales. Este AGENTS.md documenta fielmente lo que existe hoy.

## Stack Tecnológico

| Componente | Tecnología | Versión | Propósito | Verificado |
|-----------|-----------|---------|-----------|-----------|
| Lenguaje | Kotlin | 2.2.10 | Lenguaje principal del módulo | [ctx7] |
| Build | Gradle | 9.4.1 | Sistema de compilación | ✅ AGP 9.2.1 |
| Plugins | Android Gradle Plugin | 9.2.1 | Compilación Android | [ctx7] compatible con Kotlin 2.2.10 + compileSdk 36 |
| SDK mínimo | Android API | 30 (Android 11 / Wear OS 3) | Dispositivos objetivo | ✅ |
| SDK objetivo | Android API | 36 (Wear OS 6) | Versión target | [ctx7] nueva sintaxis `release(36)` |
| SDK compilación | Android API | 36 | Compilación contra API 36 | [ctx7] usa `compileSdk { version = release(36) { minorApiLevel = 1 } }` |
| UI Toolkit | Jetpack Compose para Wear | BOM 2025.12.00 | UI declarativa para Wear OS | ✅ |
| Navegación | TransformingLazyColumn | Compose Foundation 1.5.6 | Scroll translúcido para Wear | ✅ |
| Tiles | ProtoLayout | 1.3.0 | Tiles de esfera de reloj | [pendiente ctx7] |
| Tiles Material3 | ProtoLayout Material3 | 1.3.0 | Componentes Material3 para Tiles | [pendiente ctx7] |
| Complicaciones | watchface-complications | 1.2.1 | Data source para complicaciones | [pendiente ctx7] compatibilidad API 36 |
| Wear OS base | play-services-wearable | 20.0.1 | APIs base de Wear OS | ✅ |

## Arquitectura Actual

```
wearos/
├── AGENTS.md                              # Este archivo
├── README.md                              # Documentación del módulo
├── build.gradle.kts                       # Build raíz (AGP + Kotlin Compose)
├── settings.gradle.kts                    # Configuración del proyecto
├── gradle.properties                      # JVM args, configuration cache
├── gradle/
│   ├── libs.versions.toml                 # Catálogo de versiones
│   └── wrapper/
│       └── gradle-wrapper.properties      # Gradle 9.4.1 wrapper
│
└── app/
    └── src/main/
        ├── AndroidManifest.xml            # Permisos, servicios, activity
        ├── res/
        │   ├── values/
        │   │   ├── strings.xml            # Cadenas: app_name, hello_world, labels
        │   │   └── styles.xml             # SplashScreen theme
        │   ├── drawable/                  # splash_icon, launcher backgrounds
        │   └── mipmap-anydpi/             # ic_launcher, ic_launcher_round
        └── java/com/example/wearos/
            ├── presentation/
            │   ├── MainActivity.kt        # Actividad principal (115 líneas)
            │   └── theme/
            │       └── Theme.kt           # Tema MaterialTheme vacío (17 líneas)
            ├── complication/
            │   └── MainComplicationService.kt  # Complication data source (41 líneas)
            └── tile/
                └── MainTileService.kt     # Tile service (65 líneas)
```

## Estado Funcional por Archivo

| Archivo | Líneas | Tipo | Estado | ¿Qué hace? | ¿Qué le falta? |
|---------|--------|------|--------|-----------|---------------|
| `MainActivity.kt` | 115 | Placeholder | ❌ | Muestra 3 botones (A/B/C) con `onClick = { /*TODO*/ }` en un TransformingLazyColumn. Tema visual vacío. | Sensores HR/SPO2, HTTP client, telemetría, UI con datos reales, foreground service, manejo de permisos runtime |
| `MainComplicationService.kt` | 41 | Placeholder | ❌ | Retorna día de la semana (Mon-Sun) vía SuspendingComplicationDataSourceService. Usa Calendar.DAY_OF_WEEK. | Datos de salud reales (HR, riesgo), conexión a Health Services, actualización periódica con datos reales |
| `MainTileService.kt` | 65 | Placeholder | ❌ | Muestra "Hello World" vía ProtoLayout material3 primaryLayout. | Datos biométricos, estado de conexión, indicador de riesgo cardiovascular |
| `Theme.kt` | 17 | Esqueleto | ⚠️ | Wrapper vacío de `MaterialTheme()` sin personalización. | Colores corporativos, tipografía, formas (DS) |
| `AndroidManifest.xml` | 71 | Config | ⚠️ | Declara características watch, WAKE_LOCK, complication/tile services, MainActivity, standalone=true. | BODY_SENSORS, FOREGROUND_SERVICE, INTERNET, RECEIVE_BOOT_COMPLETED (ver sección de permisos) |
| `strings.xml` | 6 | Config | ⚠️ | Cadenas app_name, hello_world, tile_label, complication_label. | Cadenas para pantallas de telemetría, errores de conexión |
| `libs.versions.toml` | 48 | Config | ⚠️ | Define AGP 9.2.1, Kotlin 2.2.10, Compose BOM 2025.12.00, Tiles 1.5.0, Complication KTX 1.2.1. | health-services-client, OkHttp/Ktor, kotlinx-coroutines, Horologist |

**Total Kotlin SLOC: ~238 líneas — 100% skeleton/placeholder, cero lógica funcional.**

## Contrato de Comunicación con Backend

### POST /dispositivos — Registro del dispositivo

Registra el reloj WearOS en el sistema y obtiene un token JWT de autenticación.

- **URL:** `http://{BACKEND_URL}/dispositivos`
- **Método:** POST
- **Auth:** Ninguna (registro inicial)
- **Request body:**
  ```json
  {
    "tipo": "WearOS",
    "modelo": "Galaxy Watch 6",
    "sistemaOperativo": "Wear OS 6",
    "paciente_id": 1
  }
  ```
- **Response (201):**
  ```json
  {
    "id": 1,
    "tipo": "WearOS",
    "modelo": "Galaxy Watch 6",
    "sistemaOperativo": "Wear OS 6",
    "tokenAutenticacion": "eyJhbGciOiJIUzI1NiIs...",
    "activo": true,
    "ultimoHeartbeat": null,
    "paciente_id": 1
  }
  ```

**Esquema Pydantic (backend/app/schemas/dispositivo.py):**
```python
class DispositivoCreate(BaseModel):
    tipo: str
    modelo: str
    sistemaOperativo: str
    paciente_id: int

class DispositivoRead(BaseModel):
    id: int
    tipo: str
    modelo: str
    sistemaOperativo: str
    tokenAutenticacion: str
    activo: bool
    ultimoHeartbeat: Optional[datetime]
    paciente_id: int
```

### POST /telemetria — Envío de datos biométricos

Envía las lecturas de sensores del reloj al backend.

- **URL:** `http://{BACKEND_URL}/telemetria`
- **Método:** POST
- **Auth:** `Authorization: Bearer <tokenAutenticacion>` (JWT del dispositivo)
- **Request body:**
  ```json
  {
    "frecuenciaCardiaca": 72.0,
    "spo2": 98.0,
    "anomaliaEcg": null,
    "timestamp": "2026-06-16T10:00:00",
    "dispositivo_id": 1
  }
  ```
- **Response (201):**
  ```json
  {
    "id": 42,
    "frecuenciaCardiaca": 72.0,
    "anomaliaEcg": null,
    "spo2": 98.0,
    "timestamp": "2026-06-16T10:00:00",
    "estadoProcesamiento": "validada",
    "dispositivo_id": 1,
    "evento_id": null
  }
  ```

**Esquema Pydantic (backend/app/schemas/dispositivo.py):**
```python
class TelemetriaCreate(BaseModel):
    frecuenciaCardiaca: float
    anomaliaEcg: Optional[str] = None
    spo2: float
    timestamp: datetime
    dispositivo_id: int
```

- **Validaciones del backend** (`telemetria_service.py`): 30 ≤ frecuenciaCardiaca ≤ 220, 0 ≤ spo2 ≤ 100
- **Errores:** 422 si datos inválidos, 404 si dispositivo no existe
- **Códigos de estado:** `estadoProcesamiento` = "recibida" → "validada" tras validación exitosa

### Autenticación JWT

| Propiedad | Valor |
|-----------|-------|
| Generación | `create_device_token(device_id: int)` en `backend/app/core/security.py` |
| Algoritmo | HS256 (simétrico) |
| Claims | `sub` = str(device_id), `type` = "device", `exp` = 30 días |
| SECRET_KEY | Hardcodeada en `settings.py` (debe cambiarse a variable de entorno) |
| Envío | Header `Authorization: Bearer <token>` en cada POST /telemetria |

### WebSocket /ws/telemetria/{paciente_id}

El backend emite broadcasts en tiempo real a los dashboards conectados cuando recibe telemetría.

- **URL:** `ws://{BACKEND_URL}/ws/telemetria/{paciente_id}?token={tokenJWT}`
- **Mensaje broadcast:**
  ```json
  {
    "tipo": "telemetria",
    "fc": 72.0,
    "spo2": 98.0,
    "timestamp": "2026-06-16T10:00:00"
  }
  ```

### Umbrales de Alerta

**Archivo `backend/app/config/umbrales.json`:**
```json
{
  "umbrales": {
    "fc_max": 120,
    "fc_min": 40,
    "spo2_min": 90,
    "oldpeak_max": 2.0
  },
  "ventana_evento_minutos": 5,
  "ventana_evento_anomalia_minutos": 1,
  "clasificacion": {
    "bajo": 0.3,
    "medio": 0.7
  }
}
```

Nota: `telemetria_service.py` valida HR en rango 30-220 (más permisivo que umbrales.json que define fc_min=40, fc_max=120).

## Permisos Android

### Declarados actualmente en AndroidManifest.xml

| Permiso | Estado | Declarado en | Propósito |
|---------|--------|-------------|-----------|
| `android.hardware.type.watch` | ✅ | Manifest | Característica: es un reloj |
| `android.permission.WAKE_LOCK` | ✅ | Manifest | Mantener CPU activa |

### Requeridos y NO declarados

| Permiso | Requerido para | Prioridad |
|---------|---------------|-----------|
| `android.permission.BODY_SENSORS` | Health Services API (API ≤ 35). Declarar con `maxSdkVersion="35"`. | 🔴 Alta |
| `android.permission.health.READ_HEART_RATE` | Reemplaza BODY_SENSORS en API 36+. Permiso moderno. | 🔴 Alta |
| `android.permission.FOREGROUND_SERVICE` | Servicio en primer plano para captura continua de HR | 🔴 Alta |
| `android.permission.FOREGROUND_SERVICE_HEALTH` | Tipo específico para datos de salud en foreground service | 🔴 Alta |
| `android.permission.INTERNET` | Comunicación HTTP con backend (POST /telemetria) | 🔴 Alta |
| `android.permission.ACCESS_NETWORK_STATE` | Verificar conectividad antes de enviar datos | 🟡 Media |
| `android.permission.RECEIVE_BOOT_COMPLETED` | Auto-inicio del servicio al encender el reloj | 🟡 Media |
| `android.permission.READ_HEALTH_DATA_IN_BACKGROUND` | Reemplaza BODY_SENSORS_BACKGROUND en API 36+ para HR en background | 🟡 Media |
| `android.permission.ACTIVITY_RECOGNITION` | Opcional para detección de actividad del paciente | 🔵 Baja |

### Permisos Runtime (solicitados en código)

Además del manifest, algunos permisos deben solicitarse en tiempo de ejecución:
- `HealthPermissions.READ_HEART_RATE` (API 36+) — solicitar antes de acceder a HR
- `BODY_SENSORS` (API ≤ 35) — solicitar en runtime
- `ACTIVITY_RECOGNITION` — solicitar en runtime si se usa

## Dependencias Gradle

### Presentes en libs.versions.toml

| Dependencia | Versión | Propósito |
|------------|---------|-----------|
| AGP | 9.2.1 | Plugin de compilación Android |
| Kotlin Compose Plugin | 2.2.10 | Plugin Compose para Kotlin |
| play-services-wearable | 20.0.1 | APIs base de Wear OS |
| Compose BOM | 2025.12.00 | Material3 (wear), Foundation (wear), UI, Graphics |
| Wear Compose Material3 | 1.5.6 | Componentes Material3 para Wear |
| Wear Compose Foundation | 1.5.6 | Foundation para Wear (TransformingLazyColumn) |
| Tiles | 1.5.0 | ProtoLayout Tiles API |
| Tiles Renderer | 1.5.0 | Renderizado de Tiles en preview |
| ProtoLayout | 1.3.0 | Layout system para Tiles |
| ProtoLayout Material3 | 1.3.0 | Componentes Material3 para Tiles |
| Complication KTX | 1.2.1 | Data source para complicaciones |
| Activity Compose | 1.13.0 | Integración Activity + Compose |
| Core Splashscreen | 1.2.0 | Pantalla de splash |
| Guava | 33.2.1-android | ListenableFuture para Tiles API |

### Ausentes (necesarias para funcionalidad real)

| Dependencia | Versión sugerida | Propósito | Prioridad |
|------------|-----------------|-----------|-----------|
| `androidx.health:health-services-client` | [pendiente ctx7] | Health Services API (PassiveMonitoringClient, MeasureClient) | 🔴 Alta |
| `com.squareup.okhttp3:okhttp` | 5.4.0 | Cliente HTTP para comunicación con backend | 🔴 Alta |
| `org.jetbrains.kotlinx:kotlinx-coroutines-android` | [pendiente ctx7] | Corrutinas para tareas asíncronas (HTTP, sensores) | 🔴 Alta |
| `androidx.room:room-ktx` | [pendiente ctx7] | Almacenamiento local para cola offline de telemetría | 🟡 Media |
| `androidx.datastore:datastore-preferences` | [pendiente ctx7] | Almacenamiento de token JWT y preferencias | 🟡 Media |
| `com.google.android.horologist` | [pendiente ctx7] | Utilidades para Wear OS (scrunch, scroll, etc.) | 🔵 Baja |

## Flujo de Datos del Sistema

### Ruta principal (WearOS → Backend → Dashboard)

```
WearOS ──POST /telemetria──▶ Backend (FastAPI :8000)
                                │
                                ├──▶ Valida (rangos HR 30-220, SPO2 0-100)
                                ├──▶ Almacena en PostgreSQL (tabla telemetrias)
                                ├──▶ WebSocket broadcast a dashboards
                                └──▶ n8n webhook (ruta paralela)
```

### Ruta completa con evaluación de riesgo

```
WearOS ──▶ Backend ──▶ PostgreSQL
                │
                └──▶ n8n webhook workflow
                        │
                        └──▶ POST /evaluar ──▶ Microservice (FastAPI :8001)
                                                    │
                                                    ├──▶ RiskEngine (RandomForest)
                                                    ├──▶ Si threshold > 0.7 → alerta
                                                    └──▶ Telegram al médico de guardia
```

### Relación con n8n

**Rutas paralelas, no secuenciales.** WearOS y n8n son fuentes de datos independientes:

- **WearOS** → envía POST /telemetria directamente al backend
- **n8n** → recibe webhooks IoT simulados (THA-Webhook-Telemetria) y también escribe a la misma tabla `telemetrias`

Ambos caminos comparten la misma tabla PostgreSQL pero entran por endpoints distintos. n8n NO es un intermediario obligatorio para los datos de WearOS.

### Estado offline

**Actualmente no hay manejo de conectividad perdida.** Si WearOS pierde conexión con el backend:
- Los datos biométricos no capturados se pierden
- No hay cola offline ni almacenamiento local
- No hay reintento automático (retry)
- No hay indicación visual de desconexión en la UI

## Convenciones del Módulo

- **Archivos Kotlin:** PascalCase (MainActivity.kt, Theme.kt)
- **Archivos XML:** snake_case (AndroidManifest.xml, strings.xml)
- **Paquetes:** `com.example.wearos.{categoria}` (presentation, complication, tile)
- **Servicios:** Sufijo `Service` (MainComplicationService, MainTileService)
- **Tema:** `WearosTheme` como wrapper de MaterialTheme
- **UI:** Jetpack Compose para Wear (Wear Compose Material3)
- **Preview:** `@WearPreviewDevices` y `@WearPreviewFontScales`
- **Nombres de recursos:** `app_name`, `hello_world` (snake_case)
- **Estado:** los archivos nuevos en camelCase siguiendo el patrón Kotlin

## Integración con otros módulos

```
WearOS ─── REST/HTTP ──▶ Backend (POST /telemetria, POST /dispositivos)
Backend ◀─── WebSocket ──▶ WearOS (broadcast /ws/telemetria/{id})
Backend ─── PostgreSQL ──▶ n8n (misma tabla telemetrias)
```

- **Con backend:** HTTP vía POST /telemetria con token Bearer JWT del dispositivo
- **Con n8n:** Sin conexión directa. Ambos escriben a la misma tabla vía backend.
- **Con microservice:** Sin conexión directa. Backend/media via n8n webhook que llama POST /evaluar.
- **Con frontend:** Sin conexión directa. Los datos llegan al dashboard via WebSocket del backend.

## Seguridad

### Estado actual

| Aspecto | Estado | Notas |
|---------|--------|-------|
| Autenticación WearOS→Backend | ⚠️ Definido pero no implementado en WearOS | Backend tiene JWT (HS256, 30 días). WearOS no tiene HTTP client. |
| SECRET_KEY del backend | ❌ Hardcodeada | `settings.py`: "triaje-cardiovascular-secret-key-change-in-production" |
| INTERNAL_TOKEN | ❌ Hardcodeada | `settings.py`: "dev-token-cambiar-en-prod" |
| CORS | ⚠️ Abierto | `allow_origins=["*"]` en backend y microservice |
| Credenciales BD | ❌ Versionadas | backend/.env, microservice/.env, n8n/.env contienen credenciales reales Aiven |

### Pendiente para WearOS

| Aspecto | Requerido |
|---------|-----------|
| BACKEND_URL como configuración externa | .env o .env.example con variable de entorno |
| Token JWT almacenado seguro | DataStore (no SharedPreferences cifrado) |
| Certificados SSL/Hostname verification | OkHttp por defecto verifica certificados |

## Tests

**Backend:** `tests/test_telemetria.py` — 2 tests que validan POST /telemetria (rango válido e inválido) vía httpx AsyncClient.

**WearOS:** No existen tests automatizados. El módulo no tiene estructura de pruebas configurada.

## Recursos de Referencia

- [Health Services API — Guía oficial](https://developer.android.com/health-and-fitness/guides/health-services)
- [Health Services — Passive monitoring](https://developer.android.com/health-and-fitness/guides/health-services/monitor-background)
- [Health Services — Permisos](https://developer.android.com/health-and-fitness/guides/health-services/permissions)
- [Wear OS Compose Material3](https://developer.android.com/jetpack/compose/ wear)
- [OkHttp](https://square.github.io/okhttp/)
- [Diagrama UML del Sistema](../../Documents/Diagrama%20UML.md)
