## Why

El backend del sistema de triaje cardiovascular IoT no existe. Es el núcleo de la arquitectura: orquesta la telemetría desde dispositivos WearOS, persiste datos clínicos en PostgreSQL (Supabase), expone una API REST para el dashboard médico, y se comunica con el microservicio de IA para predicción de riesgo. Sin backend no hay demo viable para la entrega académica.

## What Changes

- Crear proyecto base FastAPI con SQLModel, Alembic, pydantic-settings y asyncpg.
- Implementar **12 modelos SQLModel** (Usuario, Paciente, Medico, Perfil, Triaje, Alerta, Log, Patologia, Historial, Dispositivo, Telemetria, Evento) con **FK simple (1:1)** entre Usuario y Paciente/Medico — NO herencia de tablas.
- Crear schemas Pydantic v2 para request/response de todas las entidades.
- Implementar **auth JWT** (`python-jose` + `passlib[bcrypt]`) para médicos y tokens rotables JWT para dispositivos WearOS.
- Crear **8 services** con lógica de negocio: auth, paciente, triaje, alerta, evento, dispositivo, telemetria, microservice_client.
- Crear **10 routers** REST + **1 WebSocket** (`/ws/telemetria/{paciente_id}`) para telemetría en tiempo real.
- Configurar **umbrales de riesgo** vía `app/config/umbrales.json` (bajo < 0.3, medio < 0.7, alto ≥ 0.7) con ventana de evento de 5 minutos (configurable por tipo).
- Implementar cliente HTTP async (`httpx.AsyncClient`) para comunicación con el microservicio de predicción.
- Configurar migraciones Alembic con **dos URLs PostgreSQL**: async (`postgresql+asyncpg://`) para la app y sync (`postgresql://`) para migraciones.
- Crear suite de tests con pytest (~8 archivos + conftest.py).
- **Total estimado**: ~48 archivos, ~2,460 líneas, ~12 horas de implementación.

## Capabilities

### New Capabilities
- `backend-core`: Proyecto base, configuración, conexión a BD, dependencias compartidas.
- `backend-auth`: Autenticación JWT para médicos y tokens rotables para dispositivos WearOS.
- `backend-pacientes`: CRUD de pacientes, médicos, perfiles, patologías e historiales médicos.
- `backend-triaje`: Creación, consulta y atención de triajes con notificación Telegram y escalamiento de urgencia.
- `backend-alertas`: Ciclo de vida de alertas (emitir, leer, asignar médico, atender).
- `backend-telemetria`: Recepción de telemetría desde WearOS, validación, enriquecimiento y asignación a eventos.
- `backend-websocket`: WebSocket `/ws/telemetria/{paciente_id}` para broadcast de telemetría en tiempo real al frontend.
- `backend-microservice-client`: Cliente HTTP async para solicitar predicciones al microservicio de IA.

### Modified Capabilities
- *(ninguno — no existen capabilities previos para este módulo)*

## Impact

- **Código**: Todo nuevo en `Project/backend/app/` (~40 archivos) y `Project/backend/tests/` (~9 archivos).
- **Dependencias**: 14 paquetes Python nuevos (FastAPI 0.136.3, SQLModel 0.0.37, Pydantic 2.12.2, Alembic, python-jose, passlib[bcrypt], pytest, httpx, NumPy, asyncpg, pydantic-settings, uvicorn[standard], psycopg2-binary, websockets).
- **Requiere Python ≥ 3.10** (FastAPI 0.129+ drop Python 3.9).
- **Base de datos**: PostgreSQL remoto en Supabase (async para app, sync para Alembic).
- **Demo**: El backend es requisito para la demo de 10 min + 5 min Q&A (máximo 30 pacientes simulados).
- **Riesgos resueltos**: Herencia SQLModel (FK simple), URLs async/sync PostgreSQL, Python 3.10+.
