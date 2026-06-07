## ADDED Requirements

### Requirement: Proyecto base FastAPI con SQLModel
El sistema SHALL crear un proyecto FastAPI 0.136.3 con SQLModel 0.0.37, pydantic-settings, Alembic y asyncpg. La estructura de carpetas SHALL seguir la guía "Bigger Applications" de FastAPI.

#### Scenario: Iniciar servidor de desarrollo
- **WHEN** se ejecuta `uvicorn app.main:app --reload`
- **THEN** el servidor inicia sin errores y responde con `{ }` en `GET /`

### Requirement: Configuración centralizada via pydantic-settings
El sistema SHALL leer variables de entorno desde `.env` usando `pydantic-settings`. SHALL soportar `DATABASE_URL` (sync) y `DATABASE_URL_ASYNC` (async).

#### Scenario: Cargar configuración desde .env
- **WHEN** se instancia `Settings()`
- **THEN** los atributos `DATABASE_URL` y `DATABASE_URL_ASYNC` contienen las URLs de PostgreSQL configuradas en `.env`

### Requirement: Conexión async a PostgreSQL
El sistema SHALL crear un engine async con `create_async_engine` usando `postgresql+asyncpg://` y una session factory con `AsyncSession`.

#### Scenario: Crear engine async
- **WHEN** se importa `app.core.database`
- **THEN** el engine async está configurado con el driver `asyncpg` y `echo=False`

### Requirement: Dependencias compartidas
El sistema SHALL exponer `get_db()` como dependencia FastAPI que provee una `AsyncSession` y la cierra automáticamente.

#### Scenario: Inyectar sesión de BD en endpoint
- **WHEN** un router declara `db: AsyncSession = Depends(get_db)`
- **THEN** cada request recibe una sesión nueva y se cierra al finalizar

### Requirement: Migraciones Alembic con driver sync
El sistema SHALL configurar Alembic con `postgresql://` (psycopg2-binary) para migraciones. El `env.py` SHALL usar la URL síncrona de `Settings`.

#### Scenario: Crear y aplicar migración inicial
- **WHEN** se ejecuta `alembic revision --autogenerate -m "init"` seguido de `alembic upgrade head`
- **THEN** se crean todas las tablas definidas en los modelos SQLModel en la base de datos PostgreSQL
