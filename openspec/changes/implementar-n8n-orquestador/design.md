## Context

El proyecto Telemetry Heart AI tiene el backend 100% implementado (FastAPI, SQLModel, PostgreSQL Aiven Cloud, JWT, WebSocket) pero carece del módulo n8n que es **obligatorio** para el Nivel 1 de la rúbrica académica. Sin n8n la nota es 0.0 automáticamente.

La documentación existente (`Project/n8n/AGENTS.md`, 360 líneas, calificación 10/10) define completamente el stack, arquitectura, flujos de trabajo, prompt del LLM, variables de entorno y convenciones. Sin embargo, la exploración con ctx7 reveló **6 hallazgos críticos** que deben corregirse durante la implementación:

1. **Credenciales PostgreSQL incorrectas**: `.env.example` apunta a Supabase pero el backend real usa Aiven Cloud.
2. **Versión n8n desactualizada**: AGENTS.md dice "2.23.0" pero ctx7 no verifica esa versión; `latest` es más seguro.
3. **7 variables de entorno faltantes**: `GENERIC_TIMEZONE`, `TZ`, `N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS`, `N8N_RUNNERS_ENABLED`, `DB_POSTGRESDB_SSL_REJECT_UNAUTHORIZED`, `N8N_LOG_LEVEL`, `N8N_LOG_OUTPUT`.
4. **Sin API keys**: No hay `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN` ni `LLM_API_KEY` en el entorno.
5. **PostgreSQL alcanzable**: Aiven Cloud responde en puerto 10104 desde esta máquina Linux.
6. **Nodo nativo OpenAI vs HTTP Request**: ctx7 confirma que n8n tiene nodo `n8n-nodes-base.openAi` nativo, pero AGENTS.md usa HTTP Request para flexibilidad multi-proveedor.

## Goals / Non-Goals

**Goals:**
- Desplegar contenedor n8n con Docker Compose conectado a PostgreSQL Aiven Cloud vía SSL.
- Implementar flujo principal "THA - Asistente LLM" con 15 nodos: Telegram Trigger → identificar médico → LLM genera SQL → PostgreSQL → manejo de errores con reintento → formatear respuesta → Telegram Reply → logging.
- Implementar flujo secundario "THA - Schedule Pendientes" con 7 nodos: revisión cada 5 min de triajes sin atender, notificación Telegram, actualización de flags.
- Implementar flujo secundario "THA - Webhook Telemetría" con 5 nodos: recepción POST, persistencia en BD, notificación a microservicio.
- Cada flujo genera logs en tabla `logs` con `tipoEvento` prefijado `n8n_`.
- Filtrar todo acceso por `medico_id` basado en relaciones UML (REGLA DE ORO).

**Non-Goals:**
- No modificar código del backend (n8n se conecta directo a PostgreSQL, no usa API REST).
- No implementar el microservicio (N2 LangChain / N3 Metaheurísticas) — solo notificarlo vía HTTP.
- No implementar frontend ni WearOS.
- No calcular riesgo cardiovascular en n8n (eso es del microservicio).
- No usar SQLite en ningún módulo (PostgreSQL obligatorio).

## Decisions

### 1. Imagen Docker: `docker.n8n.io/n8nio/n8n:latest` (no versión fija)
**Rationale**: El AGENTS.md propone `2.23.0` pero ctx7 no puede verificar esa versión específica. La última versión documentada con ejemplos concretos en ctx7 es `1.81.0`. Usar `latest` garantiza obtener la versión estable más reciente al momento del deploy. Pinning a una versión sin verificación ctx7 viola la Directiva de Prioridad de Verdad.
**Alternativa considerada**: Pin a `1.81.0` — rechazada porque `1.81.0` podría no ser la más reciente y no garantiza parches de seguridad.

### 2. Nodo HTTP Request para LLM (no nodo nativo OpenAI)
**Rationale**: Aunque ctx7 confirma que n8n tiene nodo `n8n-nodes-base.openAi` nativo, el diseño del AGENTS.md usa HTTP Request para poder cambiar entre OpenAI y Claude sin rehacer el workflow. HTTP Request también permite controlar exactamente el formato del prompt (system + user messages) y parsear `choices[0].message.content` directamente. El nodo nativo abstrae demasiado y no permite el prompt engineering detallado que requiere la REGLA DE ORO (`medico_id` en WHERE).
**Alternativa considerada**: Nodo nativo OpenAI — rechazado porque no soporta fácilmente el patrón de "dos llamadas al LLM" (generar SQL + formatear) con prompts diferentes y control total del body JSON.

### 3. Misma PostgreSQL del backend (no BD separada)
**Rationale**: n8n se conecta DIRECTAMENTE a la PostgreSQL de Aiven Cloud donde el backend ya tiene todas las tablas (`usuarios`, `pacientes`, `medicos`, `triajes`, `alertas`, `logs`, etc.). Esto evita sincronización de datos, replicaación, o APIs intermedias. Las credenciales se copian del `Project/backend/.env` al `Project/n8n/.env` (mismo servidor, usuario distinto si es necesario, pero misma instancia).
**Alternativa considerada**: Contenedor PostgreSQL local para n8n — rechazada porque violaría la REGLA ABSOLUTA de PostgreSQL único y crearía desincronización de datos.

### 4. Variables de entorno: agregar las 7 descubiertas por ctx7
**Rationale**: `GENERIC_TIMEZONE` y `TZ` son obligatorias para que el Schedule Trigger funcione en la zona horaria correcta (`America/Bogota`). `N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true` es una mejora de seguridad recomendada por ctx7. `N8N_RUNNERS_ENABLED=true` es requerido en versiones recientes. `DB_POSTGRESDB_SSL_REJECT_UNAUTHORIZED=false` es **crítico** porque Aiven Cloud requiere SSL y sin esta variable n8n rechazará la conexión. `N8N_LOG_LEVEL=info` y `N8N_LOG_OUTPUT=console` facilitan debugging.

### 5. Manejo de errores SQL: reintento con LLM + log fatal
**Rationale**: El LLM puede generar SQL sintácticamente incorrecto (columnas inexistentes, JOINs mal formados). En lugar de fallar silenciosamente, el flujo captura el error, lo envía al LLM para regenerar el SQL corregido, reintenta una vez, y si falla de nuevo envía una disculpa al médico y genera un log `n8n_sql_fatal`. Esto maximiza la robustez sin intervención humana.
**Alternativa considerada**: Fallback a mensaje estático sin reintento — rechazada porque no aprovecha la capacidad del LLM para auto-corregirse.

### 6. LLM genera SQL dinámico (no flujos predefinidos)
**Rationale**: El médico puede preguntar cualquier cosa: "¿Cómo está el paciente 1?", "Mis alertas pendientes", "Status general". No es posible predefinir flujos para todas las consultas. El LLM interpreta la intención, conoce el esquema de BD, y genera SQL óptimo. El prompt incluye el esquema completo + reglas de acceso, haciendo al LLM un "experto SQL" contextualizado.
**Alternativa considerada**: Flujos predefinidos para cada tipo de pregunta — rechazada porque no escala y limita la utilidad del asistente.

## Risks / Trade-offs

| Risk | Impact | Mitigation |
|------|--------|------------|
| **LLM alucina SQL** a pesar del prompt bien diseñado | Alto: el médico recibe datos incorrectos o el flujo falla | (1) Filtro `medico_id` obligatorio en prompt. (2) Reintento automático con feedback de error. (3) Log `n8n_sql_fatal` para auditoría. (4) Limitar privilegios del usuario PostgreSQL de n8n a solo SELECT/INSERT (no DELETE/UPDATE en tablas críticas). |
| **Sin API keys disponibles** | Bloqueante: flujo principal no funciona sin LLM ni Telegram | Documentar pasos explícitos para obtener: TELEGRAM_BOT_TOKEN de @BotFather, LLM_API_KEY de platform.openai.com. Incluir en checklist pre-deploy. |
| **Aiven Cloud requiere SSL** | Medio: n8n puede rechazar conexión si SSL no está configurado | Agregar `DB_POSTGRESDB_SSL_REJECT_UNAUTHORIZED=false` al `.env`. Verificar conectividad con `pg_isready` antes del deploy. |
| **`host.docker.internal` en Linux** | Medio: Docker en Linux no resuelve `host.docker.internal` por defecto | En `docker-compose.yml` agregar `--add-host host.docker.internal:host-gateway` o usar `extra_hosts`. Verificar conectividad al backend antes de activar nodos HTTP que llamen al backend. |
| **Telegram requiere chat IDs reales** | Medio: sin `telegramChatId` en tabla `medicos`, n8n ignora todos los mensajes | Script de migración o endpoint del backend para que el médico registre su `telegramChatId`. Documentar proceso en AGENTS.md. |
| **Microservicio no existe** | Bajo: webhook de telemetría llama a `MICROSERVICE_URL` que devuelve 404/timeout | El nodo HTTP Request tiene timeout de 10s. El flujo captura el error, genera log `n8n_micro_error`, y continúa. No bloquea el flujo. |
| **N8N_ENCRYPTION_KEY expuesta** | Medio: si `.env` se filtra, credenciales de n8n quedan comprometidas | `.env` en `.gitignore`. Generar key con `openssl rand -hex 32`. Documentar que nunca se versione. |

## Migration Plan

**Deploy (Fase 1 - Infraestructura):**
1. `cp Project/n8n/.env.example Project/n8n/.env`
2. Editar `.env` con credenciales reales de Aiven Cloud (copiar de `Project/backend/.env`)
3. `openssl rand -hex 32` → pegar en `N8N_ENCRYPTION_KEY`
4. `docker compose up -d` en `Project/n8n/`
5. Verificar: `curl http://localhost:5678/health`

**Deploy (Fase 2 - Flujo Principal):**
6. Abrir `http://localhost:5678`
7. Crear workflow "THA - Asistente LLM"
8. Agregar 15 nodos según tabla del AGENTS.md
9. Configurar credenciales: Telegram Bot, PostgreSQL, HTTP Request (LLM)
10. Guardar y activar workflow
11. Probar con curl simulando mensaje de Telegram (o usar el trigger real)

**Deploy (Fase 3 - Flujos Secundarios):**
12. Crear workflow "THA - Schedule Pendientes" (7 nodos)
13. Crear workflow "THA - Webhook Telemetría" (5 nodos)
14. Probar schedule con botón "Execute Workflow" manualmente
15. Probar webhook con `curl -X POST http://localhost:5678/webhook/telemetria -d '{...}'`

**Tablas internas de n8n en PostgreSQL**

n8n crea automáticamente sus propias tablas en la base de datos PostgreSQL configurada. Las principales son:

| Tabla              | Propósito                                           |
|--------------------|-----------------------------------------------------|
| stored_credentials | Credenciales cifradas (Telegram token, LLM API key) |
| workflow_entity    | Definiciones de workflows                           |
| execution_entity   | Historial de ejecuciones                            |
| tag_entity         | Etiquetas para workflows                            |
| user               | Usuarios de n8n                                     |

Estas tablas NO conflictúan con las tablas del backend (`usuarios`, `pacientes`, `medicos`, `triajes`, `logs`, etc.). Tienen nombres completamente diferentes y n8n nunca modifica tablas que no haya creado él mismo.

Si se desea aislar completamente, se puede crear un schema separado en PostgreSQL (ej: `n8n_schema`). Pero para la demo no es necesario — n8n y el backend conviven en el mismo database sin conflictos.

**Rollback:**
- `docker compose down` en `Project/n8n/` detiene el contenedor.
- Los workflows se pierden si no se exportan: usar "Download" en la UI de n8n para guardar JSONs en `Project/n8n/workflows/`.
- Los logs en PostgreSQL (`logs` tabla) persisten — no se pierden.

## Open Questions Resueltas

**Q1: ¿Qué proveedor LLM usar?**
Decisión: **OpenAI gpt-4o-mini**.
Justificación: Es el modelo más rentable con buena calidad de generación SQL. Tiene contexto de 128k tokens, suficiente para el esquema de 12 tablas + la pregunta del médico. El diseño soporta cambiar a Claude vía `LLM_BASE_URL` sin rehacer el workflow.
Costo estimado: ~$0.15 por 1M tokens de input, ~$0.60 por 1M tokens de output. Cada consulta del médico consume ~500-1000 tokens. Presupuesto mensual estimado: < $5 para uso de demo.

**Q2: ¿Rate limiting en el LLM?**
Decisión: **No implementar rate limiting en esta fase**.
Justificación: El proyecto tiene ~30 pacientes simulados y 1-2 médicos. No se espera carga suficiente para exceder los límites de OpenAI (5,000 RPM en tier gratuito). Si en el futuro se escala, se puede agregar un nodo Function en n8n que cuente requests por minuto y retrase llamadas al LLM.
Riesgo: Si se excede el límite, la API devuelve HTTP 429. El nodo HTTP Request captura el error y el médico recibe "Lo siento, no pude procesar tu consulta."

**Q3: ¿Cómo registra el médico su telegramChatId?**
Decisión: **Endpoint en el backend: PUT /medicos/{id}/telegram-chat-id**.
Justificación: Es la opción más segura y controlada. Un médico autenticado (JWT) registra su chat ID contra su propio perfil. No requiere exponer la BD ni crear comandos complejos en el bot.
Implementación: Backend ya tiene PUT /medicos/{id}. Extender el schema `MedicoUpdate` para incluir `telegramChatId` opcional. El médico se loguea en el backend, obtiene su JWT, y ejecuta:
```bash
curl -X PUT http://localhost:8000/medicos/{id} \
  -H "Authorization: Bearer {JWT}" \
  -H "Content-Type: application/json" \
  -d '{"telegramChatId": "123456789"}'
```
Opción B (descartada): Comando `/start` en el bot de Telegram — requeriría que el médico se autentique dentro del chat, lo que implica manejar contraseñas en Telegram o enviar un token por correo. Demasiado complejo para la demo.
Opción C (descartada): Migración manual SQL — no escala, requiere acceso a la BD, no es defendible en Q&A.

**Q4: ¿Exportar workflows como JSON en Git?**
Decisión: **Sí. Los JSON exportados van en `Project/n8n/workflows/`**.
Justificación: Son código. Versionarlos permite tracking de cambios y reproducibilidad. Los JSON no contienen credenciales (n8n las referencia por ID de credential, no por valor).
Proceso: Después de crear cada workflow, exportar desde n8n UI (menú → Download) y guardar en `Project/n8n/workflows/<nombre>.json`.
