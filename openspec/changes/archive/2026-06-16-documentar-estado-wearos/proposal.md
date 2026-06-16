## Why

El módulo WearOS tiene un `AGENTS.md` de 3 líneas que declara "gestión de adquisición de datos y telemetría IoT — capturar señales biométricas pasivas — transmitir de forma segura", pero la realidad es 100% skeleton/placeholder. Sin documentación precisa del estado actual, cualquier agente que intervenga en el módulo asumirá funcionalidad inexistente, generará código sobre suposiciones falsas y producirá fricción técnica. Actualizar el AGENTS.md para reflejar fielmente lo que existe hoy elimina esa ambigüedad de raíz.

## What Changes

- Reescribir `Project/wearos/AGENTS.md` para documentar fielmente el estado actual del módulo WearOS
- Actualizar la sección de wearos en `Project/AGENTS.md` (raíz) para reflejar el estado real
- No se modifica código Kotlin, ni build.gradle, ni AndroidManifest, ni ningún archivo de implementación
- No hay cambios en backend, microservice, frontend ni n8n
- Cambio puramente documental

## Capabilities

### New Capabilities
- `documentacion-estado-actual`: Documentar el estado real del módulo WearOS en AGENTS.md: archivos existentes, lo que hace cada uno (placeholder o funcional), dependencias presentes/ausentes, permisos declarados/faltantes, y el contrato de comunicación con backend
- `documentacion-contrato-backend`: Documentar los endpoints REST que WearOS debe consumir (POST /dispositivos, POST /telemetria, WebSocket /ws/telemetria), schemas de request/response, mecanismo de autenticación JWT, y umbrales de validación del backend
- `documentacion-flujo-datos`: Documentar el flujo de datos completo del sistema que involucra a WearOS: captura → POST /telemetria → validación → WebSocket broadcast → n8n webhook → microservicio → alertas/Telegram

### Modified Capabilities
- *(ninguna — no se modifican capacidades existentes)*

## Impact

- **Archivos modificados**: `Project/wearos/AGENTS.md` (reescritura completa), `Project/AGENTS.md` (sección wearos)
- **Archivos leídos para documentación**: todos los .kt del módulo, AndroidManifest.xml, build.gradle.kts, libs.versions.toml, schemas y routers del backend, umbrales.json
- **Herramientas externas**: ctx7 MCP para verificar versiones de librerías y APIs de Wear OS / Health Services
- **Sin impacto en**: dependencias, compilación, endpoints, base de datos, infraestructura
