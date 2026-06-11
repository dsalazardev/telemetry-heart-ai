## Why

El módulo n8n es obligatorio para el Nivel 1 de la rúbrica académica (0.0–3.5). Sin n8n la nota final del proyecto es **0.0 automáticamente**. Actualmente el backend está 100% implementado pero n8n no existe: no hay contenedor Docker, no hay workflows, no hay bot de Telegram, no hay conexión a PostgreSQL. Este change desbloquea el Nivel 1 al desplegar n8n como orquestador inteligente con LLM que actúa como asistente para médicos vía Telegram.

## What Changes

- **NUEVO** `Project/n8n/docker-compose.yml`: Contenedor n8n oficial conectado a PostgreSQL remota (Aiven Cloud)
- **NUEVO** `Project/n8n/.env` (no versionado): Credenciales reales de PostgreSQL, Telegram, LLM
- **NUEVO** `Project/n8n/.env.example`: Plantilla con 23 variables documentadas
- **NUEVO** Flujo principal "THA - Asistente LLM" (15 nodos): Recibe mensaje Telegram → identifica médico → LLM genera SQL → ejecuta PostgreSQL → formatea respuesta → responde médico. Incluye manejo de errores SQL con reintento automático.
- **NUEVO** Flujo secundario "THA - Schedule Pendientes" (7 nodos): Revisa triajes sin atender cada 5 min y notifica al médico por Telegram.
- **NUEVO** Flujo secundario "THA - Webhook Telemetría" (5 nodos): Recibe telemetría POST, la almacena en BD y notifica al microservicio.
- **ACTUALIZACIÓN** `Project/n8n/AGENTS.md`: Corregir credenciales PostgreSQL (Supabase → Aiven Cloud), actualizar versión n8n (2.23.0 → latest), agregar 7 variables de entorno descubiertas por ctx7, decidir nodo nativo OpenAI vs HTTP Request.
- **ACTUALIZACIÓN** `Documents/Diagrama UML.md`: Cambiar `Adapter` de `<<microservice>>` a `<<n8n>>`.
- **NUEVO** Tabla `logs` recibe 12 tipoEvento con prefijo `n8n_` para trazabilidad completa.

## Capabilities

### New Capabilities

- `n8n-orchestrator`: Despliegue de n8n con Docker Compose, configuración de variables de entorno, conexión a PostgreSQL remota, y persistencia de credenciales encriptadas.
- `n8n-telegram-integration`: Bot de Telegram que recibe mensajes de médicos registrados, identifica al médico por `telegramChatId`, y responde solo a usuarios válidos en BD.
- `n8n-llm-sql-agent`: Pipeline de dos llamadas al LLM: (1) generar SQL dinámico con filtros `medico_id` obligatorios basados en relaciones UML, (2) formatear resultados en texto legible para Telegram. Incluye reintento automático si SQL falla.
- `n8n-scheduled-triage`: Revisión periódica cada 5 minutos de triajes `atendida=false AND telegramEnviado=false`, notificación al médico, y actualización de flags.
- `n8n-telemetry-webhook`: Endpoint webhook `/webhook/telemetria` que recibe datos de WearOS, los persiste en `telemetrias`, registra log, y dispara evaluación en microservicio vía HTTP.

### Modified Capabilities

- *(Ninguno: n8n es un módulo nuevo, no modifica capabilities existentes del backend)*

## Impact

- **Nuevo código**: `Project/n8n/docker-compose.yml`, `Project/n8n/.env.example`, workflows exportados como JSON en `Project/n8n/workflows/`.
- **Infraestructura**: Requiere contenedor Docker n8n, acceso a PostgreSQL Aiven Cloud (SSL obligatorio), token de bot de Telegram, API key de LLM (OpenAI/Claude).
- **Backend**: Sin cambios de código. n8n se conecta DIRECTAMENTE a PostgreSQL, no usa la API REST del backend. El backend ya tiene `medicos.telegramChatId`, `triajes.telegramEnviado`, y tabla `logs` con `tipoEvento`.
- **Microservicio**: El webhook de telemetría llama al microservicio en `MICROSERVICE_URL` (que aún no existe — se tolera el error y se loguea).
- **Frontend**: Sin impacto. El dashboard médico sigue funcionando independientemente.
- **WearOS**: Sin impacto directo. El webhook puede recibir datos simulados con curl.
- **Riesgos**: LLM puede alucinar SQL a pesar del prompt; Telegram requiere chat IDs reales de médicos; Aiven Cloud requiere SSL (`DB_POSTGRESDB_SSL_REJECT_UNAUTHORIZED=false`).

## Alignment with Rubric

Este change desbloquea el **Nivel 1** de la rúbrica académica (0.0 – 3.5). A continuación, el mapeo directo:

| Requisito de la Rúbrica (N1) | Cómo lo cumple este change |
|------------------------------|---------------------------|
| **Trigger de flujo** | Webhook (`/webhook/telemetria`) + Telegram Trigger (consulta médica) + Schedule Trigger (revisión periódica cada 5 min) |
| **Nodo(s) de procesamiento** | PostgreSQL (lectura/escritura directa) + HTTP Request al LLM (generación SQL) + HTTP Request al microservicio |
| **Nodo de salida** | Telegram Reply (respuesta al médico) + Log en PostgreSQL (`n8n_sql_ok`, `n8n_telegram_ok`) |
| **Captura de pantalla del flujo** | Se genera durante la implementación desde la UI de n8n (herramienta externa, no parte del código) |
| **6 pasos de creación documentados** | Se documentan en `Project/n8n/README.md` después de la implementación |
| **Video narrado (3-8 min)** | Se graba al final del proyecto (herramienta externa) |
| **JSON exportado del flujo** | `Project/n8n/workflows/*.json` — versionado en Git |
| **Métricas: nodos activos, trigger, tiempo, tasa de éxito** | Se consultan en la UI de n8n (Settings → Executions) y en la tabla `logs` de PostgreSQL (`tipoEvento LIKE 'n8n_%'`) |
