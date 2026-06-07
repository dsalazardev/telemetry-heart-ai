# AGENTS.md — Backend

## Stack Tecnológico

| Componente | Tecnología | Versión | Propósito |
|-----------|-----------|---------|-----------|
| Framework web | FastAPI | 0.136.3 | API REST async con OpenAPI automática |
| ORM | SQLModel | 0.0.37 | Modelos de BD + schemas Pydantic unificados |
| Validación | Pydantic v2 | 2.12.2 | Schemas de request/response, validación de tipos |
| Migraciones | Alembic | latest | Control de versiones del esquema de BD |
| Base de datos | PostgreSQL | — | Persistencia relacional clínica (Supabase remoto) |
| Autenticación | python-jose + passlib[bcrypt] | 3.3+ / 1.7.4 | JWT para médicos, token Bearer para dispositivos |
| Testing | pytest + httpx | 9.0.3 / 0.27.2 | Tests async con cliente HTTP |
| Estadísticas | NumPy + Pandas + SimPy | 2.3.2 / latest / 4 | Agregación de telemetría, simulación de triaje |

## Arquitectura

Limpia / Hexagonal con capas organizadas según la guía oficial de FastAPI "Bigger Applications":

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app, include routers, CORS, lifespan
│   ├── dependencies.py            # Dependencias compartidas (auth, db session)
│   ├── config.py                  # Config (settings, env vars via pydantic-settings)
│   │
│   ├── models/                    # SQLModel (tablas de BD)
│   │   ├── __init__.py
│   │   ├── usuario.py             # Usuario, Paciente, Medico (herencia joined)
│   │   ├── perfil.py
│   │   ├── triaje.py              # Triaje + Log
│   │   ├── alerta.py
│   │   ├── patologia.py           # Patologia + Historial
│   │   ├── dispositivo.py         # Dispositivo + Telemetria + Evento
│   │   └── enum.py                # Enums compartidos (nivelUrgencia, tipoEvento...)
│   │
│   ├── schemas/                   # Pydantic (request/response, no BD)
│   │   ├── __init__.py
│   │   ├── usuario.py             # UsuarioCreate, UsuarioRead, UsuarioUpdate
│   │   ├── triaje.py
│   │   ├── alerta.py
│   │   └── ...
│   │
│   ├── routers/                   # APIRouter (endpoints REST)
│   │   ├── __init__.py
│   │   ├── auth.py                # POST /login, POST /token-refresh
│   │   ├── pacientes.py           # CRUD pacientes + perfil
│   │   ├── medicos.py             # CRUD médicos
│   │   ├── triajes.py             # CRUD triajes + listar pendientes
│   │   ├── alertas.py             # CRUD alertas + marcarLeida, asignarMedico
│   │   ├── dispositivos.py        # CRUD dispositivos + revocarToken
│   │   ├── telemetria.py          # POST telemetría (desde WearOS)
│   │   ├── eventos.py             # Eventos + evaluar umbrales
│   │   ├── patologias.py          # CRUD patologías + historiales
│   │   └── logs.py                # Consulta de logs
│   │
│   ├── services/                  # Lógica de negocio
│   │   ├── __init__.py
│   │   ├── auth_service.py        # Login, JWT, verificación de tokens
│   │   ├── paciente_service.py    # Registro, perfil, generarAlertas
│   │   ├── triaje_service.py      # Crear triaje, notificarTelegram, escalarUrgencia
│   │   ├── alerta_service.py      # Ciclo de vida: marcarLeida, asignarMedico
│   │   ├── evento_service.py      # Agregar telemetría, evaluarUmbrales, disparar Workflow
│   │   ├── dispositivo_service.py # Validar token, heartbeat, revocar
│   │   ├── telemetria_service.py  # Validar, enriquecerConLab, asignar a Evento
│   │   └── microservice_client.py # Cliente HTTP para comunicación con microservicio
│   │
│   ├── core/                      # Configuración central
│   │   ├── __init__.py
│   │   ├── database.py            # Engine, session factory, get_db dependency
│   │   ├── security.py            # JWT create/verify, password hashing
│   │   └── settings.py            # pydantic-settings (env vars)
│   │
│   └── utils/                     # Utilidades
│       ├── __init__.py
│       └── estadisticas.py        # NumPy/Pandas/SimPy para simulación y demo
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Fixtures: test db, client, auth headers
│   ├── test_auth.py
│   ├── test_pacientes.py
│   ├── test_triajes.py
│   ├── test_alertas.py
│   ├── test_telemetria.py
│   ├── test_eventos.py
│   └── test_microservice_client.py
│
├── alembic/                       # Migraciones automáticas
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── requirements.txt
├── pyproject.toml
└── Dockerfile
```

## Endpoints Principales

Basados en las clases `<<backend>>` del diagrama UML:

| Recurso | Endpoints | Servicio |
|---------|-----------|----------|
| Auth | `POST /auth/login`, `POST /auth/refresh` | auth_service |
| Pacientes | `GET/POST /pacientes`, `GET/PUT/DELETE /pacientes/{id}` | paciente_service |
| Médicos | `GET/POST /medicos`, `GET/PUT/DELETE /medicos/{id}` | auth_service |
| Perfil | `GET/PUT /pacientes/{id}/perfil` | paciente_service |
| Triajes | `GET/POST /triajes`, `GET /triajes/pendientes`, `PUT /triajes/{id}/atender` | triaje_service |
| Alertas | `GET /alertas`, `PUT /alertas/{id}/leer`, `PUT /alertas/{id}/asignar` | alerta_service |
| Dispositivos | `POST /dispositivos`, `PUT /dispositivos/{id}/revocar` | dispositivo_service |
| Telemetría | `POST /telemetria` (desde WearOS) | telemetria_service |
| Eventos | `GET /eventos`, `POST /eventos/{id}/evaluar` | evento_service |
| Patologías | `GET/POST /patologias` | paciente_service |
| Historiales | `GET/POST /pacientes/{id}/historiales` | paciente_service |
| Logs | `GET /triajes/{id}/logs` | triaje_service |

## Comunicación con otros módulos

```
Backend ─── REST/HTTP ───▶ Frontend (dashboard médico)
Backend ─── REST/HTTP ───▶ Microservice (solicitar predicción)
Backend ◀─── Webhooks ───▶ n8n (workflow orquesta)
Backend ◀─── REST/JSON ──▶ WearOS (telemetría entrante)
```

- **Con microservice**: HTTP síncrono vía `httpx.AsyncClient` desde `services/microservice_client.py`
- **Con n8n**: Webhooks REST — n8n llama al backend cuando un workflow completa su ejecución
- **Con WearOS**: POST /telemetria con token Bearer del dispositivo

## Convenciones

- **Archivos**: snake_case
- **Modelos**: Singular (Paciente, Triaje) — SQLModel usa el nombre de la clase como tabla
- **Routers**: Plural (pacientes.py, triajes.py)
- **Servicios**: Sufijo `_service` (triaje_service.py)
- **Schemas**: Sufijo de operación (PacienteCreate, PacienteRead, PacienteUpdate)
- **Endpoints**: Plural (`/pacientes`, `/triajes/{id}`)
- **Tests**: Prefijo `test_` + `_` + nombre del módulo (`test_triajes.py`)
- **BD**: PostgreSQL en Supabase (remoto), conexión vía URL con python-dotenv

## Herencia Usuario → Paciente / Medico

SQLModel no tiene soporte nativo para herencia de tablas. Se implementa con **joined table inheritance** de SQLAlchemy:

```python
# models/usuario.py
class Usuario(SQLModel, table=True):
    __tablename__ = "usuarios"
    id: int = Field(primary_key=True)
    documento: str
    nombres: str
    apellidos: str
    correo: str
    password: str
    telefono: str
    activo: bool = True
    tipo: str = Field(index=True)  # "paciente" | "medico"

class Paciente(Usuario, table=True):
    __tablename__ = "pacientes"
    id: int = Field(foreign_key="usuarios.id", primary_key=True)
    fechaNacimiento: date

class Medico(Usuario, table=True):
    __tablename__ = "medicos"
    id: int = Field(foreign_key="usuarios.id", primary_key=True)
    especialidad: str
    licencia: str
    telegramChatId: str
```

## Decisiones Arquitectónicas
Ver `decisions/` para ADRs detallados de cada decisión técnica:
- [ADR-001: FastAPI vs Django](decisions/ADR-001-fastapi-vs-django.md)
- [ADR-002: SQLModel vs SQLAlchemy](decisions/ADR-002-sqlmodel-vs-sqlalchemy.md)
- [ADR-003: SQLite vs PostgreSQL](decisions/ADR-003-sqlite-vs-postgresql.md)
- [ADR-004: Joined Table Inheritance](decisions/ADR-004-joined-table-inheritance.md)
- [ADR-005: Services vs Model Methods](decisions/ADR-005-services-vs-model-methods.md)
- [ADR-006: HTTP Microservice Communication](decisions/ADR-006-httpx-microservice-communication.md)
- [ADR-007: SimPy Demo Simulation](decisions/ADR-007-simpy-demo-simulation.md)

## Mapeo UML → Código

| Concepto UML | Implementación |
|-------------|---------------|
| Clase `<<backend>>` | Modelo SQLModel en `models/` |
| Atributo `-attr: Tipo` | Columna SQLModel (`Field(...)`) |
| Método `+metodo()` | Función en `services/` |
| Relación `1 --> *` | ForeignKey + Relationship |
| Herencia `Usuario <|-- Paciente` | Joined table inheritance |
| `Workflow` (interface) | Protocol/ABC en `services/microservice_client.py` |
