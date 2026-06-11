## ADDED Requirements

### Requirement: n8n se despliega con Docker Compose
El sistema SHALL ejecutar n8n como contenedor Docker usando la imagen oficial `docker.n8n.io/n8nio/n8n:latest`, conectado a la instancia PostgreSQL remota de Aiven Cloud vía SSL.

#### Scenario: Contenedor n8n inicia correctamente
- **WHEN** se ejecuta `docker compose up -d` en `Project/n8n/`
- **THEN** el contenedor `n8n` está en estado `running`
- **AND** responde a `GET http://localhost:5678/health` con HTTP 200 en menos de 30 segundos

#### Scenario: Conexión a PostgreSQL remota exitosa
- **WHEN** el contenedor n8n inicia con `DB_TYPE=postgresdb` y credenciales de Aiven Cloud
- **THEN** n8n crea sus tablas internas (`migrations`, `credentials`, `workflows`, `executions`) en PostgreSQL sin errores
- **AND** no se usa SQLite ni PostgreSQL local contenedorizado

#### Scenario: Credenciales encriptadas
- **WHEN** el administrador configura `N8N_ENCRYPTION_KEY` generada con `openssl rand -hex 32`
- **THEN** n8n almacena credenciales (Telegram token, LLM API key) encriptadas en PostgreSQL
- **AND** el archivo `.env` con credenciales reales NO está versionado en Git

### Requirement: Variables de entorno completas
El sistema SHALL exponer todas las variables de entorno necesarias en `.env.example` y requerirlas en `.env` para el funcionamiento de n8n.

#### Scenario: Variables de entorno mínimas presentes
- **WHEN** se verifica `Project/n8n/.env`
- **THEN** contiene: `DB_POSTGRESDB_HOST`, `DB_POSTGRESDB_PORT`, `DB_POSTGRESDB_DATABASE`, `DB_POSTGRESDB_USER`, `DB_POSTGRESDB_PASSWORD`, `DB_POSTGRESDB_SSL_REJECT_UNAUTHORIZED`, `N8N_PORT`, `N8N_PROTOCOL`, `N8N_HOST`, `N8N_ENCRYPTION_KEY`, `GENERIC_TIMEZONE`, `TZ`, `N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS`, `N8N_RUNNERS_ENABLED`, `N8N_LOG_LEVEL`, `N8N_LOG_OUTPUT`, `TELEGRAM_BOT_TOKEN`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `BACKEND_URL`, `BACKEND_API_KEY`, `MICROSERVICE_URL`

#### Scenario: Credenciales PostgreSQL apuntan a Aiven Cloud
- **WHEN** se compara `Project/n8n/.env` con `Project/backend/.env`
- **THEN** `DB_POSTGRESDB_HOST` coincide con el host de Aiven Cloud (`telemetry-heart-ai-ucaldas-80c3.g.aivencloud.com`)
- **AND** `DB_POSTGRESDB_PORT` es `10104`
- **AND** no apunta a Supabase ni a ningún otro servidor PostgreSQL

### Requirement: Persistencia de datos de n8n
El sistema SHALL persistir los workflows, credenciales y ejecuciones de n8n en el volumen Docker `n8n_data` montado en `/home/node/.n8n`.

#### Scenario: Reinicio del contenedor preserva workflows
- **WHEN** se reinicia el contenedor n8n con `docker compose restart`
- **THEN** todos los workflows creados previamente están disponibles en la UI
- **AND** las credenciales configuradas (Telegram, PostgreSQL, LLM) no requieren reconfiguración
