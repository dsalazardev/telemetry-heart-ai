# AGENTS.md — n8n Workflows

## Stack Tecnológico

| Componente | Tecnología | Versión | Propósito |
|-----------|-----------|---------|-----------|
| Plataforma de automatización | n8n | 2.23.0 | Orquestación visual de flujos de trabajo |
| Despliegue | Docker Compose | latest | Contenedor de n8n con .env propio |
| Runtime | Node.js | v22.x LTS | Ejecución de nodos n8n |
| Base de datos | PostgreSQL | remota (Supabase) | **Misma BD del backend** — acceso directo |
| LLM | OpenAI / Claude API | latest | Interpreta preguntas del médico y genera SQL |
| Notificaciones | Telegram Bot API | latest | Bot que habla con médicos registrados |
| Imagen Docker | n8nio/n8n | docker.n8n.io/n8nio/n8n | Oficial estable |

## Rol de n8n

n8n actúa como **asistente inteligente**: recibe cualquier pregunta del médico por Telegram, usa un LLM para interpretarla y generar SQL, ejecuta la consulta contra PostgreSQL (con estrictos límites de acceso), y responde al médico.

n8n no tiene flujos rígidos. El médico pregunta lo que sea y el LLM decide qué consultar.

| ❌ n8n NO hace | ✅ Quién lo hace |
|----------------|----------------|
| Calcular riesgo | Microservicio (N2: LangChain, N3: Metaheurísticas) |
| Tener BD separada | No. Misma PostgreSQL del backend |
| Responder a cualquiera | Solo médicos con `telegramChatId` en BD |
| Dejar ver datos de otros médicos | **Nunca**. Toda query incluye `medico_id` |

## REGLA DE ORO: Límites por Relaciones UML

```
Relación UML:   Medico "1" --> "*" Triaje : triajes
Traducción:     triajes.medico_id = <medico_id>
Límite:         Solo ve triajes donde él sea el médico asignado

Relación UML:   Medico "1" --> "*" Alerta : alertas
Traducción:     alertas.medico_id = <medico_id>
Límite:         Solo ve alertas donde él sea el médico asignado

Relación UML:   Triaje "1" --> "*" Log : logs
Traducción:     logs.triaje_id IN (SELECT id FROM triajes WHERE medico_id = <medico_id>)
Límite:         Solo ve logs de sus propios triajes

Relación UML:   Paciente --> Triaje (via medico_id)
Traducción:     Solo ve pacientes con los que tenga triajes
```

**TODA consulta SQL generada por el LLM DEBE incluir un filtro por `medico_id`.** Cero excepciones.

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│  Médico escribe al bot de Telegram:                             │
│  "¿Cómo está el paciente 1?" / "Mis alertas" / "Status"        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ chat_id + texto
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. Telegram Trigger                            ┌─────────────┐ │
│     Recibe mensaje del médico                   │ PostgreSQL  │ │
│     { chat_id, text, message_id }               │ medicos     │ │
│         │                                       │ telegram-   │ │
│         ▼                                       │ ChatId      │ │
│  2. PostgreSQL: Obtener medico_id               └─────────────┘ │
│     SELECT id FROM medicos                                       │
│     WHERE telegramChatId = :chat_id                              │
│         │                                                       │
│         ▼                                                       │
│  3. IF: ¿Médico existe? ──No──▶ Ignorar mensaje                 │
│         │                                                       │
│        Sí                                                       │
│         ▼                                                       │
│  4. Function: Armar prompt para LLM                             │
│     { pregunta, medico_id, esquema BD, reglas acceso }          │
│         │                                                       │
│         ▼                                                       │
│  5. HTTP Request: LLM → Generar SQL                             │
│     POST https://api.openai.com/v1/chat/completions              │
│     System: "Eres un asistente SQL..."                          │
│     User: pregunta del médico                                   │
│         │                                                       │
│         ▼                                                       │
│  6. PostgreSQL: Ejecutar SQL generado                           │
│     (con medico_id = 5 en WHERE)                                │
│         │                                                       │
│         ▼                                                       │
│  7. HTTP Request: LLM → Formatear respuesta                     │
│     "Convierte estos datos en texto amigable..."                │
│         │                                                       │
│         ▼                                                       │
│  8. PostgreSQL INSERT INTO logs                                 │
│     (tipoEvento='n8n_llm', detalle='...', exitoso=true)        │
│         │                                                       │
│         ▼                                                       │
│  9. Telegram Reply: Responder al médico                         │
└─────────────────────────────────────────────────────────────────┘
```

## Flujo Principal: Asistente LLM

### Nodos

| # | Tipo | Nombre | Configuración |
|---|------|--------|---------------|
| 1 | **Telegram Trigger** | `Recibir Mensaje` | Trigger on message. Credential: Bot Token |
| 2 | **PostgreSQL** | `Identificar Médico` | `SELECT id, u.nombres, u.apellidos FROM medicos m JOIN usuarios u ON m.id = u.id WHERE m.telegramChatId = :chat_id` |
| 3 | **IF** | `¿Médico válido?` | Si `rowCount == 0` → NoOp (ignorar). Si > 0 → continuar |
| 4 | **Function** (JS) | `Armar Prompt SQL` | Construye el system prompt con esquema BD + `medico_id` + reglas de acceso |
| 5 | **HTTP Request** | `LLM → Generar SQL` | `POST {{$env.LLM_BASE_URL}}/chat/completions`. Headers: `Authorization: Bearer {{$env.LLM_API_KEY}}`. Body: prompt del paso 4 |
| 6 | **PostgreSQL** | `Ejecutar SQL` | Query: `{{ $json.choices[0].message.content }}` (el SQL que generó el LLM) |
| 7 | **IF** | `¿SQL exitoso?` | Si error → nodo 8. Si éxito → nodo 12 |
| 8 | **Function** (JS) | `Capturar Error SQL` | Extrae `error.message` del nodo PostgreSQL. Almacena `{ error, pregunta_original, intento: 1 }` |
| 9 | **HTTP Request** | `LLM → Regenerar SQL` | `POST {{$env.LLM_BASE_URL}}/chat/completions`. Prompt: "El SQL anterior falló con: {error}. Pregunta original: {pregunta}. Genera SQL corregido con las mismas reglas de acceso (medico_id = {id})." |
| 10 | **PostgreSQL** | `Reintentar SQL` | Ejecuta el SQL corregido del paso 9 |
| 11 | **IF** | `¿2do intento ok?` | Si éxito → nodo 12. Si error → Telegram Reply disculpa + nodo 15 con log fatal |
| 12 | **HTTP Request** | `LLM → Formatear` | Mismo LLM, prompt: "Convierte estos datos JSON en texto legible para Telegram..." |
| 13 | **Telegram Reply** | `Responder Médico` | Reply al `chat_id` original con el texto formateado |
| 14 | **PostgreSQL** | `INSERT Log éxito` | `INSERT INTO logs (triaje_id, tipoEvento, detalle, exitoso, errorMsg, timestamp) VALUES (NULL, 'n8n_sql_ok', $1, true, NULL, NOW())` |
| 15 | **PostgreSQL** | `INSERT Log error` | `INSERT INTO logs (triaje_id, tipoEvento, detalle, exitoso, errorMsg, timestamp) VALUES (NULL, 'n8n_sql_fatal', $1, false, $2, NOW())` |

### Prompt que n8n envía al LLM (Paso 4)

```text
Eres un asistente SQL para un sistema de triaje cardiovascular.
El médico que pregunta TIENE ID = {{medico_id}}.

REGLA ABSOLUTA: TODAS las consultas SQL deben incluir
WHERE medico_id = {{medico_id}} o el filtro equivalente.
Si la pregunta intenta acceder a datos de otro médico,
responde: "ERROR_ACCESO: No tienes permiso para ver esos datos."

Esquema de la BD:
1. usuarios: id, documento, nombres, apellidos, correo, telefono, activo, tipo
2. pacientes: id (FK→usuarios.id), fechaNacimiento
   → Solo accesible si el paciente tiene triajes con el médico
3. medicos: id (FK→usuarios.id), especialidad, licencia, telegramChatId
4. triajes: id, probabilidadRiesgo, nivelUrgencia, factoresCriticos,
   explicacionClinica, telegramEnviado, atendida, diagnosticoConfirmado,
   fechaEmision, fechaAtencion, paciente_id, medico_id
   → SIEMPRE filtrar por medico_id = {{medico_id}}
5. alertas: id, tipo, mensaje, leida, atendida, fechaEmision,
   fechaAtencion, paciente_id, medico_id, triaje_id
   → SIEMPRE filtrar por medico_id = {{medico_id}}
6. logs: id, timestamp, tipoEvento, detalle, exitoso, errorMsg, triaje_id
   → Solo accesible si triaje_id pertenece a un triaje del médico
   → Usar: triaje_id IN (SELECT id FROM triajes WHERE medico_id = {{medico_id}})
7. telemetrias: frecuenciaCardiaca, anomaliaEcg, spo2, timestamp,
   estadoProcesamiento, dispositivo_id, evento_id
   → Solo accesible a través de triajes del médico
8. eventos: id, tipo, ventanaInicio, ventanaFin, lecturas, valorAgregado
   → Solo accesible a través de triajes del médico
9. perfiles: id, edad, sexo, tipoSangre, alergias, paciente_id
10. patologias: id, codigoCie11, nombre, categoria, factorRiesgoCardiaco
11. historiales: id, fechaDiagnostico, nivelSeveridad, tratamientoActual,
    paciente_id, patologia_id
12. dispositivos: id, tipo, modelo, activo, paciente_id

Genera SOLO la consulta SQL necesaria para responder la pregunta.
No expliques nada, solo devuelve el SQL. Si no es posible con SQL,
responde: "ERROR: No puedo responder eso con los datos disponibles."
```

### Ejemplos de preguntas vs consultas generadas

| Pregunta | SQL generado | ¿Válido? |
|----------|-------------|----------|
| "Status del paciente 1" | `SELECT t.nivelUrgencia, t.probabilidadRiesgo, t.fechaEmision, u.nombres, u.apellidos FROM triajes t JOIN pacientes p ON t.paciente_id = p.id JOIN usuarios u ON p.id = u.id WHERE t.paciente_id = 1 AND t.medico_id = 5 ORDER BY t.fechaEmision DESC LIMIT 1` | ✅ |
| "Mis alertas pendientes" | `SELECT a.id, a.tipo, a.mensaje, a.fechaEmision, u.nombres, u.apellidos FROM alertas a JOIN pacientes p ON a.paciente_id = p.id JOIN usuarios u ON p.id = u.id WHERE a.medico_id = 5 AND a.atendida = false` | ✅ |
| "¿Cuántos pacientes tengo?" | `SELECT COUNT(DISTINCT t.paciente_id) FROM triajes t WHERE t.medico_id = 5` | ✅ |
| "¿Cuántos pacientes tiene el doctor 3?" | `ERROR_ACCESO: No tienes permiso para ver datos de otro médico` | ✅ (bloqueado) |
| "Dame todos los pacientes" | `SELECT DISTINCT p.id, u.nombres, u.apellidos FROM triajes t JOIN pacientes p ON t.paciente_id = p.id JOIN usuarios u ON p.id = u.id WHERE t.medico_id = 5` | ✅ |
| "Los logs del triaje 42" | `SELECT l.id, l.timestamp, l.tipoEvento, l.detalle, l.exitoso FROM logs l WHERE l.triaje_id = 42 AND l.triaje_id IN (SELECT id FROM triajes WHERE medico_id = 5)` | ✅ |
| "Historial del paciente 1" | `SELECT h.id, h.fechaDiagnostico, h.nivelSeveridad, h.tratamientoActual, p.nombre FROM historiales h JOIN patologias p ON h.patologia_id = p.id WHERE h.paciente_id = 1 AND h.paciente_id IN (SELECT paciente_id FROM triajes WHERE medico_id = 5)` | ✅ |
| "Todos los pacientes del sistema" | Sin filtro `medico_id = 5` → `ERROR_ACCESO: No tienes permiso para ver todos los pacientes` | ✅ (bloqueado) |
| "Dime el correo del médico 3" | Intenta acceder a `medico_id = 3` → `ERROR_ACCESO: No tienes permiso para ver datos de otro médico` | ✅ (bloqueado) |

### Logs generados por este flujo

| tipoEvento | Cuándo se genera | Detalle ejemplo |
|-----------|------------------|-----------------|
| `n8n_llm_query` | El médico envía una pregunta | "Médico ID 5 preguntó: Status paciente 1" |
| `n8n_sql_ok` | SQL se ejecuta correctamente (1er intento) | "SELECT ... LIMIT 1" |
| `n8n_sql_error` | SQL falla en el 1er intento | "column xxx does not exist" |
| `n8n_sql_reintento` | SQL corregido se ejecuta en el 2do intento | "SQL corregido ejecutado correctamente" |
| `n8n_sql_fatal` | SQL falla en ambos intentos | "SQL falló en 2 intentos. Consulta abandonada" |
| `n8n_telegram_ok` | Respuesta enviada al médico | "Respuesta enviada al chat 123456789" |
| `n8n_telegram_error` | Fallo al enviar mensaje Telegram | "Bot blocked by user" |

## Variables de Entorno

`TELEGRAM_CHAT_ID` no va en el .env — se obtiene de la BD. Se agregan variables para el LLM.

| Variable | Propósito |
|----------|-----------|
| `DB_POSTGRESDB_HOST` | Host PostgreSQL remoto |
| `DB_POSTGRESDB_PORT` | Puerto PostgreSQL |
| `DB_POSTGRESDB_DATABASE` | Nombre BD |
| `DB_POSTGRESDB_USER` | Usuario BD |
| `DB_POSTGRESDB_PASSWORD` | Contraseña BD |
| `N8N_PORT` | Puerto del servidor n8n |
| `N8N_PROTOCOL` | Protocolo (http/https) |
| `N8N_HOST` | Host del servidor n8n |
| `N8N_ENCRYPTION_KEY` | Clave para cifrar credenciales almacenadas en la BD de n8n (Telegram token, LLM API key). Generar con: `openssl rand -hex 32` |
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram |
| `LLM_BASE_URL` | URL de la API del LLM (ej: `https://api.openai.com/v1`) |
| `LLM_API_KEY` | API Key del LLM |
| `LLM_MODEL` | Modelo del LLM (ej: `gpt-4o`, `gpt-4o-mini`) |
| `BACKEND_URL` | URL del backend FastAPI |
| `BACKEND_API_KEY` | API Key o JWT para auth contra backend |
| `MICROSERVICE_URL` | URL del microservicio LangChain |

## Instalación con Docker Compose

```yaml
version: "3.8"
services:
  n8n:
    image: docker.n8n.io/n8nio/n8n
    ports:
      - "${N8N_PORT}:5678"
    environment:
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=${DB_POSTGRESDB_HOST}
      - DB_POSTGRESDB_PORT=${DB_POSTGRESDB_PORT}
      - DB_POSTGRESDB_DATABASE=${DB_POSTGRESDB_DATABASE}
      - DB_POSTGRESDB_USER=${DB_POSTGRESDB_USER}
      - DB_POSTGRESDB_PASSWORD=${DB_POSTGRESDB_PASSWORD}
      - N8N_PROTOCOL=${N8N_PROTOCOL}
      - N8N_HOST=${N8N_HOST}
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
    env_file:
      - .env
    volumes:
      - n8n_data:/home/node/.n8n
    restart: unless-stopped

volumes:
  n8n_data:
```

Sin PostgreSQL aparte. n8n se conecta directo al remoto.

## Mapeo al Diagrama UML

| Clase UML | Relación | Cómo lo aplica n8n |
|-----------|----------|-------------------|
| `Medico` `"1" --> "*" Triaje` | `triajes.medico_id = ?` | Toda query sobre triajes incluye `WHERE medico_id = {id}` |
| `Medico` `"1" --> "*" Alerta` | `alertas.medico_id = ?` | Toda query sobre alertas incluye `WHERE medico_id = {id}` |
| `Triaje` `"1" --> "*" Log` | `logs.triaje_id IN (subquery)` | Solo logs de triajes donde `medico_id = {id}` |
| `Paciente` `"1" --> "*" Triaje` | vía `triajes.medico_id` | Solo pacientes con triajes del médico |
| `Workflow` | `<<Interface>>` | n8n implementa `ejecutarFlujo` y `notificarUrgencia` |
| `Adapter` | **`<<n8n>>`** | Implementación concreta de Workflow |

**Nota:** La clase `Adapter` en el UML actual está como `<<microservice>>` — debe actualizarse a `<<n8n>>`.

## Decisiones Técnicas

| # | Decisión | Justificación |
|---|----------|---------------|
| 1 | LLM genera SQL dinámico | El médico pregunta lo que sea. No hay flujos fijos que cubran todos los casos |
| 2 | `medico_id` siempre en WHERE | Basado en relaciones UML: cada médico solo ve sus datos |
| 3 | Dos llamadas al LLM (generar SQL + formatear) | 1) Precisión: generar SQL requiere pensamiento lógico puro; formatear requiere tono amigable. Separarlos evita que un formato creativo contamine la generación SQL. 2) Costo: la segunda llamada puede usar un modelo más barato (gpt-4o-mini vs gpt-4o). 3) Debuggabilidad: si el SQL falla, el error está en la primera llamada, no en la segunda. |
| 4 | Médico identificado por `telegramChatId` | Cada médico tiene su chat ID. n8n no responde a nadie sin registro |
| 5 | Prompt incluye esquema completo + reglas | El LLM necesita conocer la estructura de la BD y los límites de acceso |
| 6 | Misma PostgreSQL del backend | Sin BD separada. n8n se conecta directo al PostgreSQL remoto |
| 7 | Cada acción genera INSERT INTO logs | Trazabilidad completa de todas las operaciones de n8n |
| 8 | Docker Compose sin PostgreSQL | n8n se conecta al remoto. No necesita postgres contenedorizado |

## Convenciones

- **Workflow**: "THA - Asistente LLM"
- **Path webhook**: `/webhook/telemetria`
- **Logs**: `tipoEvento` con prefijo `n8n_` (`n8n_llm`, `n8n_log`)
- **Variables**: Prefijo `$env.` en expresiones n8n
- **Chat ID**: Siempre extraído de `medicos.telegramChatId`, nunca hardcodeado
- **Prompt engineering**: El prompt del LLM se arma en un Function node con JS puro (template strings)

## Prerrequisitos

| Recurso | Detalle |
|---------|---------|
| **Docker** | `docker --version` → 24+ |
| **Docker Compose** | `docker compose version` → 2.0+ |
| **PostgreSQL remoto** | Acceso a la BD compartida del backend (ver `Project/backend/.env`) |
| **Bot de Telegram** | Creado con @BotFather. Token guardado como `TELEGRAM_BOT_TOKEN` |
| **API Key LLM** | OpenAI o Claude. URL base y modelo definidos en `.env` |
| **Red** | Los contenedores deben alcanzar `host.docker.internal`. En Linux: `--add-host host.docker.internal:host-gateway` |

## Quick Start

```bash
# 1. Clonar .env.example y configurar credenciales
cp .env.example .env
nano .env

# 2. Generar encryption key para credenciales de n8n
openssl rand -hex 32   # Pegar en N8N_ENCRYPTION_KEY

# 3. Iniciar n8n
docker compose up -d

# 4. Abrir navegador
open http://localhost:5678

# 5. Crear workflow "THA - Asistente LLM"
# Agregar nodos según la sección "Flujo Principal" más arriba
```

## Flujo Secundario 1: Revisión Periódica de Triajes Pendientes

Notifica al médico automáticamente cuando hay triajes sin atender, sin que él tenga que preguntar.

### Trigger

Schedule: `*/5 * * * *` (cada 5 minutos). Modo: disabled por defecto, se activa manualmente para la demo.

### Nodos

| # | Tipo | Nombre | Configuración |
|---|------|--------|---------------|
| 1 | **Schedule Trigger** | `Cada 5 minutos` | Cron: `*/5 * * * *` |
| 2 | **PostgreSQL** | `Triajes Pendientes` | `SELECT t.id, t.nivelUrgencia, t.probabilidadRiesgo, t.paciente_id, u.nombres, u.apellidos, m.telegramChatId FROM triajes t JOIN pacientes p ON t.paciente_id = p.id JOIN usuarios u ON p.id = u.id JOIN medicos m ON t.medico_id = m.id WHERE t.atendida = false AND t.telegramEnviado = false` |
| 3 | **IF** | `¿Hay pendientes?` | Si `rowCount == 0` → INSERT log `n8n_schedule_empty` y fin. Si > 0 → loop por cada fila |
| 4 | **Function** (JS) | `Armar Alerta` | Construye markdown: `🚨 ALERTA CARDIOVASCULAR\nPaciente: {nombre}\nNivel: {nivel} ({probabilidad}%)\nTriaje ID: {id}\nFecha: {fecha}` |
| 5 | **Telegram** | `Notificar Médico` | Chat ID: `medico.telegramChatId` (del SELECT). Message: alerta formateada |
| 6 | **PostgreSQL** | `UPDATE telegramEnviado` | `UPDATE triajes SET telegramEnviado = true WHERE id = $1` |
| 7 | **PostgreSQL** | `INSERT Log Schedule` | `INSERT INTO logs (triaje_id, tipoEvento, detalle, exitoso, timestamp) VALUES ($1, 'n8n_schedule', $2, true, NOW())` |

### Logs generados por este flujo

| tipoEvento | Cuándo | Detalle |
|-----------|--------|---------|
| `n8n_schedule_ok` | Hay triajes pendientes | "Revisión periódica: 3 triajes pendientes notificados" |
| `n8n_schedule_empty` | No hay triajes pendientes | "Revisión periódica: 0 triajes pendientes" |

## Flujo Secundario 2: Recepción de Telemetría (Webhook)

Recibe datos desde WearOS (o simulación con curl), los almacena en BD y dispara la evaluación del microservicio.

### Trigger

Webhook POST externo en `/webhook/telemetria`.

### Nodos

| # | Tipo | Nombre | Configuración |
|---|------|--------|---------------|
| 1 | **Webhook** | `Recibir Telemetría` | POST, path `/webhook/telemetria`. Body: `{ paciente_id, frecuenciaCardiaca, spo2, anomaliaEcg }`. Respond: "Respond to Webhook" |
| 2 | **PostgreSQL** | `INSERT Telemetría` | `INSERT INTO telemetrias (frecuenciaCardiaca, spo2, anomaliaEcg, timestamp, estadoProcesamiento, dispositivo_id) VALUES ($1, $2, $3, NOW(), 'recibida', (SELECT id FROM dispositivos WHERE paciente_id = $4 AND activo = true LIMIT 1))` |
| 3 | **PostgreSQL** | `INSERT Log Webhook` | `INSERT INTO logs (triaje_id, tipoEvento, detalle, exitoso, timestamp) VALUES (NULL, 'n8n_webhook', $1, true, NOW())` |
| 4 | **HTTP Request** | `Notificar Microservicio` | `POST {{$env.MICROSERVICE_URL}}/evaluar`. Body: `{ paciente_id, frecuenciaCardiaca, spo2, anomaliaEcg }`. Timeout: 10s |
| 5 | **IF** | `¿Microservicio ok?` | Rama success → INSERT Log `n8n_micro_ok`. Rama error → INSERT Log `n8n_micro_error` |

### Logs generados por este flujo

| tipoEvento | Cuándo | Detalle |
|-----------|--------|---------|
| `n8n_webhook_ok` | Telemetría almacenada | "Telemetría paciente 1: FC=120, SpO2=88" |
| `n8n_micro_ok` | Microservicio responde | "Evaluación enviada al microservicio para paciente 1" |
| `n8n_micro_error` | Microservicio falla | "Error al contactar microservicio para paciente 1: timeout" |
