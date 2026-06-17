## Context

El módulo WearOS tiene un `AGENTS.md` de 3 líneas que declara "capturar señales biométricas pasivas y transmitirlas de forma segura", pero el código real es 100% placeholder: 4 archivos .kt con ~238 líneas, sin sensores, sin HTTP, sin foreground service, sin datos biométricos reales. El backend (FastAPI :8000) ya tiene los endpoints `POST /dispositivos`, `POST /telemetria` y `WS /ws/telemetria/{id}` implementados, con autenticación JWT y validación de rangos. Sin un AGENTS.md preciso, cualquier agente futuro que intervenga en el módulo asumirá funcionalidad inexistente.

**Stakeholders**: agentes de IA que intervengan el módulo WearOS, desarrolladores humanos, equipo de Sistemas Inteligentes 1 — Universidad de Caldas.

## Goals / Non-Goals

**Goals:**
- Documentar el estado real de cada archivo .kt del módulo WearOS (qué hace, qué NO hace, si es placeholder)
- Documentar el stack tecnológico actual con versiones exactas verificadas
- Documentar dependencias Gradle presentes y ausentes
- Documentar permisos Android declarados y faltantes
- Documentar el contrato completo de comunicación con el backend (endpoints, schemas, auth, validaciones)
- Documentar el flujo de datos del sistema donde WearOS participa
- Actualizar la referencia en `Project/AGENTS.md` raíz

**Non-Goals:**
- No se escribe ni modifica código Kotlin
- No se añaden ni modifican dependencias Gradle
- No se modifican permisos de AndroidManifest
- No se implementa ninguna capacidad nueva (sensores, HTTP, servicios)
- No se generan tareas de implementación ni plan de desarrollo
- No se modifican backend, microservice, frontend ni n8n

## Decisions

| Decisión | Opción elegida | Alternativas | Razón |
|----------|---------------|-------------|-------|
| Estructura del AGENTS.md | Tabla de Stack Tecnológico + Arquitectura de archivos + Contrato backend | Texto libre, bullet list | El patrón de `Project/backend/AGENTS.md` usa tabla + secciones jerárquicas y funciona bien. Consistencia entre módulos. |
| Sección de estado por archivo | Tabla: archivo, líneas, tipo (placeholder/funcional), qué hace, qué le falta | Párrafo narrativo | Una tabla da visibilidad inmediata del esqueleto. |
| Sección de permisos Android | Tabla: permiso, declarado (sí/no), requerido para | Lista separada | Contraste directo entre el manifest actual y lo que Health Services API requiere. Facilita ver la brecha. |
| Verificación de versiones | Marcar cada versión con `[ctx7]` si requiere verificación | Asumir correctas | Las versiones de librerías cambian; ctx7 es la fuente de verdad del proyecto. |
| Contrato backend | Schemas Pydantic literales (código Python) | Descripción textual | El código fuente en backend define el contrato; reproducirlo textualmente evita desviación. |

## Risks / Trade-offs

- **[Staleness]** Las versiones documentadas pueden quedar desactualizadas. → Mitigación: incluir nota de "última verificación: fecha" y referencia a ctx7 como fuente de verdad.
- **[ctx7 availability]** Si ctx7 no está disponible al validar, las versiones no pueden verificarse. → Mitigación: marcar todas las versiones no verificadas con `[pendiente ctx7]`.
- **[Scope creep]** Podría surgir la tentación de empezar a implementar al ver la brecha documentada. → Mitigación: los non-goals son explícitos — cero implementación.
