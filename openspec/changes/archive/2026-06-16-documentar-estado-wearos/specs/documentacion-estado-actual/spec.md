## ADDED Requirements

### Requirement: Documentar stack tecnológico del módulo
El AGENTS.md SHALL incluir una tabla con el stack tecnológico del módulo WearOS: componentes, tecnologías, versiones exactas y propósito de cada una.

#### Scenario: Stack completo con versiones
- **WHEN** un agente lee el AGENTS.md
- **THEN** encuentra AGP 9.2.1, Kotlin 2.2.10, compileSdk 36, minSdk 30, targetSdk 36, Compose BOM 2025.12.00, Gradle 9.4.1

### Requirement: Documentar arquitectura de archivos
El AGENTS.md SHALL listar todos los archivos .kt del módulo con su ruta, número de líneas, propósito funcional y estado actual (placeholder, esqueleto, o funcional).

#### Scenario: Cada archivo .kt tiene su entrada
- **WHEN** un agente revisa la sección de arquitectura
- **THEN** encuentra MainActivity.kt (115 líneas, placeholder), MainComplicationService.kt (41 líneas, placeholder), MainTileService.kt (65 líneas, placeholder), Theme.kt (17 líneas, esqueleto vacío)

### Requirement: Documentar estado funcional por archivo
El AGENTS.md SHALL indicar explícitamente qué funcionalidad TIENE cada archivo y qué funcionalidad LE FALTA, sin prescribir implementación.

#### Scenario: Estado de MainActivity
- **WHEN** un agente consulta el estado de MainActivity
- **THEN** la documentación indica que tiene 3 botones con onClick vacío, cero sensores, cero HTTP, cero datos reales

#### Scenario: Estado de Complication
- **WHEN** un agente consulta el estado de MainComplicationService
- **THEN** la documentación indica que retorna día de la semana, sin datos de salud

#### Scenario: Estado de Tile
- **WHEN** un agente consulta el estado de MainTileService
- **THEN** la documentación indica que muestra "Hello World", sin datos biométricos

### Requirement: Documentar dependencias Gradle
El AGENTS.md SHALL listar las dependencias presentes y ausentes en libs.versions.toml, marcando las ausentes necesarias para el contrato con backend.

#### Scenario: Dependencias presentes
- **WHEN** un agente consulta dependencias
- **THEN** encuentra play-services-wearable 20.0.1, Compose Material3 1.5.6, Tiles 1.5.0, Complication KTX 1.2.1, ProtoLayout 1.3.0

#### Scenario: Dependencias ausentes
- **WHEN** un agente consulta dependencias faltantes
- **THEN** encuentra health-services-client, OkHttp/Ktor, kotlinx-coroutines, Horologist

### Requirement: Documentar permisos Android
El AGENTS.md SHALL listar los permisos declarados en AndroidManifest.xml y los permisos requeridos por el backend y Health Services API que no están declarados.

#### Scenario: Permisos declarados
- **WHEN** un agente consulta permisos
- **THEN** encuentra WAKE_LOCK como único permiso declarado

#### Scenario: Permisos faltantes
- **WHEN** un agente consulta permisos faltantes
- **THEN** encuentra BODY_SENSORS, FOREGROUND_SERVICE, INTERNET, RECEIVE_BOOT_COMPLETED como no declarados
