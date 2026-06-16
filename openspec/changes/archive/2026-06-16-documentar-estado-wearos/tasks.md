## 1. Leer archivos fuente del módulo WearOS

- [x] 1.1 Leer y analizar los 4 archivos .kt del módulo (MainActivity, MainComplicationService, MainTileService, Theme)
- [x] 1.2 Leer AndroidManifest.xml y strings.xml
- [x] 1.3 Leer build.gradle.kts, libs.versions.toml, settings.gradle.kts, gradle.properties, gradle-wrapper.properties
- [x] 1.4 Leer README.md y AGENTS.md actuales

## 2. Leer archivos de contrato con backend

- [x] 2.1 Leer schemas/dispositivo.py (TelemetriaCreate, DispositivoCreate)
- [x] 2.2 Leer routers/telemetria.py y routers/dispositivos.py
- [x] 2.3 Leer models/dispositivo.py y services/telemetria_service.py
- [x] 2.4 Leer security.py (create_device_token) y umbrales.json
- [x] 2.5 Leer n8n/workflows/THA-Webhook-Telemetria.json

## 3. Verificar versiones contra ctx7

- [x] 3.1 [ctx7] health-services-client: PassiveMonitoringClient confirmado para background HR. MeasureClient para tiempo real. Usar DataType.HEART_RATE_BPM.
- [x] 3.2 [ctx7] OkHttp 5.4.0 recomendado para Wear OS. Tiene módulo okhttp-coroutines para corrutinas. Bien establecido.
- [ ] 3.3 [pendiente ctx7] SuspendingComplicationDataSourceService en API level 36
- [ ] 3.4 [pendiente ctx7] ProtoLayout material3 1.3.0 con compileSdk 36
- [x] 3.5 [ctx7] Foreground Service: usar FOREGROUND_SERVICE + FOREGROUND_SERVICE_HEALTH. Tipo: health.
- [x] 3.6 [ctx7] Health Services API: BODY_SENSORS con maxSdkVersion=35 + android.permission.health.READ_HEART_RATE para API 36+. READ_HEALTH_DATA_IN_BACKGROUND reemplaza BODY_SENSORS_BACKGROUND.
- [x] 3.7 [ctx7] AGP 9.2.1 + Kotlin 2.2.10 + compileSdk 36 (release API) son compatibles. compileSdk usa nueva sintaxis release(36).

## 4. Escribir AGENTS.md del módulo WearOS

- [x] 4.1 Redactar sección Stack Tecnológico (tabla con versiones verificadas)
- [x] 4.2 Redactar sección Arquitectura Actual (árbol de directorios + tabla por archivo con estado)
- [x] 4.3 Redactar sección Estado Funcional por archivo (placeholder vs funcional)
- [x] 4.4 Redactar sección Contrato de Comunicación con Backend (endpoints, schemas, auth, WS)
- [x] 4.5 Redactar sección Permisos Android (declarados vs requeridos)
- [x] 4.6 Redactar sección Dependencias Gradle (presentes vs ausentes)
- [x] 4.7 Redactar sección Flujo de Datos del Sistema (WearOS → backend → n8n → microservice)
- [x] 4.8 Redactar sección Convenciones del Módulo
- [x] 4.9 Redactar sección Integración con n8n (rutas paralelas)

## 5. Actualizar Project/AGENTS.md raíz

- [x] 5.1 Actualizar la línea de wearos en el índice de Divulgación Progresiva
- [x] 5.2 Verificar consistencia entre la referencia raíz y el nuevo AGENTS.md del módulo

## 6. Validar artefactos finales

- [x] 6.1 Verificar que todos los archivos .kt son mencionados en la documentación
- [x] 6.2 Verificar que todos los endpoints del contrato backend están documentados
- [x] 6.3 Verificar que las versiones marcadas con ctx7 están verificadas o pendientes
- [x] 6.4 Verificar que no hay referencias a funcionalidad que no existe en el código
