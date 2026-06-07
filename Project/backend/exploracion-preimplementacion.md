# Exploración Pre-Implementación — Backend

**Fecha:** 2026-06-07 (v2 — decisiones resueltas)
**Objetivo:** Determinar el estado actual y lo necesario para comenzar a implementar el backend

---

## 1. Estado Actual

### Qué existe
```
Project/backend/
├── AGENTS.md          ← Documentación completa (stack, arquitectura, ADRs, mapeo UML)
├── README.md          ← Responsabilidad y límites del módulo
├── .env               ← Conexión a Supabase PostgreSQL configurada
├── decisions/         ← 7 ADRs (decisiones técnicas documentadas)
│   ├── ADR-001-fastapi-vs-django.md
│   ├── ADR-002-sqlmodel-vs-sqlalchemy.md
│   ├── ADR-003-sqlite-vs-postgresql.md
│   ├── ADR-004-joined-table-inheritance.md    ← ✅ ACTUALIZADO (FK Simple 1:1)
│   ├── ADR-005-services-vs-model-methods.md
│   ├── ADR-006-httpx-microservice-communication.md
│   └── ADR-007-simpy-demo-simulation.md
└── (no hay código aún)
```

### Qué falta (TODO total)

| Capa | Archivos | Estado |
|------|----------|--------|
| `app/` | `__init__.py`, `main.py`, `dependencies.py` | ❌ No existen |
| `app/models/` | 7 archivos (usuario, perfil, triaje, alerta, patologia, dispositivo, enum) | ❌ No existen |
| `app/schemas/` | ~5 archivos | ❌ No existen |
| `app/routers/` | 10 archivos (+ WebSocket) | ❌ No existen |
| `app/services/` | 8 archivos | ❌ No existen |
| `app/core/` | 4 archivos (database, security, settings, __init__) | ❌ No existen |
| `app/utils/` | 1 archivo (estadisticas.py) | ❌ No existe |
| `app/config/` | 1 archivo (umbrales.json) | ❌ No existe |
| `tests/` | ~8 archivos + conftest | ❌ No existen |
| `alembic/` | env.py + versions/ | ❌ No existe |
| `requirements.txt` | — | ❌ No existe |
| `pyproject.toml` | — | ❌ No existe |

### Conexión a Supabase

El archivo `.env` tiene credenciales para Supabase PostgreSQL. Se usarán DOS URLs:

- **Async** (para la app FastAPI): `postgresql+asyncpg://postgres:...@host:5432/postgres`
- **Sync** (para Alembic): `postgresql://postgres:...@host:5432/postgres`

En `app/core/settings.py`:
```python
class Settings(BaseSettings):
    DATABASE_URL: str
    DATABASE_URL_ASYNC: str

    class Config:
        env_file = "../.env"
```

---

## 2. Verificación de Versiones (ctx7)

| Dependencia | Versión | Nota |
|------------|---------|------|
| **FastAPI** | 0.136.3 | Drop Python 3.9 desde v0.129. Requiere **Python ≥ 3.10**. |
| **SQLModel** | 0.0.37 | Construido sobre SQLAlchemy + Pydantic v2. Sin breaking changes. |
| **Pydantic** | 2.12.2 | v2.13.0b1 en beta. Usar la stable. |
| **Alembic** | latest | Sin cambios relevantes. |
| **python-jose** | 3.3+ | Production/Stable. |
| **passlib[bcrypt]** | 1.7.4 | En mantenimiento. Alternativa: `bcrypt` directo. |
| **pytest** | 9.0.3 | Confirmado. |
| **httpx** | 0.27.2 | Sin breaking changes desde 0.27. |
| **NumPy** | 2.3.2 | Soporta Python 3.11-3.14. |
| **asyncpg** | latest | Driver async PostgreSQL. |
| **pydantic-settings** | v2.12+ | Para variables de entorno. |
| **uvicorn[standard]** | latest | Servidor ASGI. |
| **psycopg2-binary** | latest | Driver sync para Alembic. |
| **websockets** | latest | Para WebSocket (FastAPI ya trae soporte vía Starlette, pero requiere el paquete). |

### Python: 3.10+ requerido

FastAPI 0.129.0+ dropped Python 3.9. FastAPI 0.136.3 requiere Python ≥ 3.10. Recomendado: **Python 3.11** o **3.12**.

Verificar con:
```bash
python --version   # debe ser 3.10 o superior
```

---

## 3. Mapeo UML → Tablas (12 clases <<backend>>)

### Diseño de herencia: FK simple (NO joined table)

```
DECISIÓN: FK simple 1:1 entre Usuario y Paciente/Medico.

Usuario es una tabla independiente. Paciente y Medico tienen FK a Usuario.
En código Python NO heredan — son modelos separados con Relationship().
```

```python
class Usuario(SQLModel, table=True):
    __tablename__ = "usuarios"
    id: int = Field(primary_key=True)
    documento: str = Field(unique=True, index=True)
    nombres: str
    apellidos: str
    correo: str = Field(unique=True, index=True)
    password: str
    telefono: str
    activo: bool = True
    tipo: str = Field(index=True)  # "paciente" | "medico"

class Paciente(SQLModel, table=True):
    __tablename__ = "pacientes"
    id: int = Field(foreign_key="usuarios.id", primary_key=True)
    fechaNacimiento: date
    usuario: Usuario = Relationship()

class Medico(SQLModel, table=True):
    __tablename__ = "medicos"
    id: int = Field(foreign_key="usuarios.id", primary_key=True)
    especialidad: str
    licencia: str
    telegramChatId: str
    usuario: Usuario = Relationship()
```

**¿Qué se pierde?** La herencia de clases en Python (`class Paciente(Usuario)`). En la práctica no se necesita: los datos comunes están en `usuario` (vía `Relationship()`), y los específicos en `paciente` o `medico`.

**¿Por qué?** SQLModel no soporta herencia de tablas. La sintaxis `class Paciente(Usuario, table=True)` mezcla SQLAlchemy y SQLModel de forma que no funciona correctamente. FK simple es SQLModel puro, funciona, se entiende, y se defiende en Q&A.

### Orden de creación (por dependencias de FK)

```
FASE 1: Tablas base (sin FKs externas)
  1. usuarios
  2. perfiles
  3. patologias

FASE 2: Tablas que referencian Usuario
  4. pacientes (FK→usuarios)
  5. medicos (FK→usuarios)

FASE 3: Tablas con FKs a Fase 1-2
  6. historiales (FK→pacientes, FK→patologias)
  7. dispositivos (FK→pacientes)

FASE 4: Tablas del flujo de triaje
  8. telemetrias (FK→dispositivos)
  9. eventos (FK→workflow externo)
  10. alertas (FK→pacientes, FK→medicos, FK→triajes)

FASE 5: Tablas finales
  11. triajes (FK→pacientes, FK→medicos, FK→workflow, FK→alertas)
  12. logs (FK→triajes)
```

### Tabla detallada

| # | Clase UML | Tabla BD | Atributos SQLModel | FKs | Métodos → Services |
|---|-----------|----------|-------------------|-----|-------------------|
| 1 | **Usuario** | `usuarios` | id: int PK, documento: str, nombres: str, apellidos: str, correo: str, password: str, telefono: str, activo: bool, tipo: str | — | — |
| 2 | **Paciente** | `pacientes` | id: int PK FK, fechaNacimiento: date, usuario: Usuario (Relationship) | id → usuarios | `registrarIngreso()`, `generarAlertas()` → paciente_service |
| 3 | **Medico** | `medicos` | id: int PK FK, especialidad: str, licencia: str, telegramChatId: str, usuario: Usuario (Relationship) | id → usuarios | `atenderAlerta()`, `listarPendientes()` → triaje_service |
| 4 | **Perfil** | `perfiles` | id: int PK, edad: int, sexo: str, tipoSangre: str, alergias: str, paciente_id: int FK | paciente_id → pacientes | — |
| 5 | **Triaje** | `triajes` | id PK, probabilidadRiesgo: float, nivelUrgencia: str, factoresCriticos: str, explicacionClinica: str, telegramEnviado: bool, atendida: bool, **diagnosticoConfirmado: bool?**, fechaEmision: datetime, fechaAtencion: datetime?, workflow_id: int?, paciente_id: int, medico_id: int?, alerta_id: int? | paciente_id, medico_id, alerta_id | `notificarTelegram()`, `escalarUrgencia()` → triaje_service |
| 6 | **Alerta** | `alertas` | id PK, tipo: str, mensaje: str, leida: bool, atendida: bool, fechaEmision: datetime, fechaAtencion: datetime?, paciente_id: int, medico_id: int?, triaje_id: int? | paciente_id, medico_id, triaje_id | `marcarLeida()`, `asignarMedico()` → alerta_service |
| 7 | **Log** | `logs` | id PK, timestamp: datetime, tipoEvento: str, detalle: str, exitoso: bool, errorMsg: str?, triaje_id: int | triaje_id → triajes | `registrar()` → triaje_service |
| 8 | **Patologia** | `patologias` | id PK, codigoCie11: str, nombre: str, categoria: str, factorRiesgoCardiaco: bool, pesoRiesgoModelo: float | — | `esFactorDeRiesgo()` → paciente_service |
| 9 | **Historial** | `historiales` | id PK, fechaDiagnostico: date, nivelSeveridad: str, controlada: bool, tratamientoActual: str, observaciones: str, ultimaRevision: datetime, paciente_id: int, patologia_id: int | paciente_id, patologia_id | `actualizarTratamiento()` → paciente_service |
| 10 | **Dispositivo** | `dispositivos` | id PK, tipo: str, modelo: str, sistemaOperativo: str, **tokenAutenticacion: str (JWT)**, activo: bool, ultimoHeartbeat: datetime?, paciente_id: int | paciente_id → pacientes | `enviarTelemetria()` → telemetria_service; `revocarToken()` → dispositivo_service |
| 11 | **Telemetria** | `telemetrias` | id PK, frecuenciaCardiaca: float, anomaliaEcg: str, spo2: float, timestamp: datetime, estadoProcesamiento: str, dispositivo_id: int, evento_id: int? | dispositivo_id → dispositivos, evento_id → eventos | `validar()`, `enriquecerConLab()` → telemetria_service |
| 12 | **Evento** | `eventos` | id PK, tipo: str, ventanaInicio: datetime, ventanaFin: datetime, lecturas: int, **valorAgregado: JSON**, workflow_id: int? | workflow_id → externo | `evaluarUmbrales()` → evento_service |

### Notas sobre las columnas

- **JSON fields**: `valorAgregado: dict = Field(sa_type=JSON)`. SQLModel lo soporta vía `sqlalchemy.JSON`.
- **ObjectId → int**: Los IDs son `int` autoincrementales.
- **Boolean nullable**: `diagnosticoConfirmado: bool | None` (null=pendiente, true=enfermo, false=sano).
- **List~Tipo~**: Relaciones OneToMany via `Relationship()`.
- **tokenAutenticacion**: JWT (ver sección 6, pregunta 3).
- **workflow_id**: Columna para referencia externa (el Workflow no es tabla BD, es interfaz). El valor es un identificador de flujo (ID del webhook de n8n o del chain de LangChain).

---

## 4. Orden de Implementación Recomendado

### Fase 0: Proyecto base (~30 min)
```
1. requirements.txt (todas las dependencias)
2. app/__init__.py + app/main.py (FastAPI app vacía)
3. app/core/settings.py (pydantic-settings con DATABASE_URL y DATABASE_URL_ASYNC)
4. app/core/database.py (engine async con asyncpg + session factory)
5. app/dependencies.py (get_db)
6. alembic init + env.py con DATABASE_URL (sync) para migraciones
7. Verificar: uvicorn app.main:app --reload → "{ }"
```

### Fase 1: Modelos + Schemas (~2h)
```
1. app/models/__init__.py
2. app/models/usuario.py (Usuario, Paciente, Medico — FK simple, SIN herencia)
3. app/models/perfil.py
4. app/models/patologia.py + historial.py
5. app/models/dispositivo.py (Dispositivo, Telemetria, Evento)
6. app/models/triaje.py (Triaje, Log, Alerta)
7. app/models/enum.py
8. app/config/umbrales.json (config inicial de umbrales y ventanas)
9. Alembic: primera migración
10. Verificar: alembic upgrade head → tablas en Supabase
```

### Fase 2: Core + Auth (~1.5h)
```
1. app/core/security.py (JWT creation/verificación, password hashing)
2. app/schemas/ (request/response por entidad)
3. app/routers/auth.py (POST /auth/login, /auth/refresh)
4. app/services/auth_service.py
5. Tests: test_auth.py
```

### Fase 3: CRUD pacientes + médicos (~2h)
```
1. app/services/paciente_service.py
2. app/routers/pacientes.py
3. app/routers/medicos.py
4. Tests: test_pacientes.py
```

### Fase 4: Triaje + Alertas (~2h)
```
1. app/services/triaje_service.py
2. app/routers/triajes.py
3. app/services/alerta_service.py
4. app/routers/alertas.py
5. Tests: test_triajes.py, test_alertas.py
```

### Fase 5: Telemetría + Eventos + WebSocket (~2.5h)
```
1. app/services/telemetria_service.py
2. app/services/evento_service.py
3. app/routers/telemetria.py (incluye WS /ws/telemetria/{paciente_id})
4. app/routers/eventos.py
5. Tests: test_telemetria.py, test_eventos.py
```

### Fase 6: Comunicación microservicio (~1h)
```
1. app/services/microservice_client.py (httpx.AsyncClient)
2. Integrar llamado a microservicio en evento_service
3. Tests: test_microservice_client.py
```

### Fase 7: Demo + SimPy (~1h)
```
1. app/utils/estadisticas.py (SimPy simulation con datos del CSV)
2. Script de demo
```

### Estimación total: ~12 horas (sin contar imprevistos)

---

## 5. Riesgos Identificados y Resueltos

### ~🔴 R1: Herencia en SQLModel (RESUELTO)~

**Decisión final: FK simple (NO joined table inheritance).**

| Aspecto | Antes (descartado) | Ahora (aprobado) |
|---------|-------------------|-------------------|
| Patrón | Joined table inheritance (SQLAlchemy) | FK simple (SQLModel puro) |
| Código | `class Paciente(Usuario, table=True)` | `class Paciente(SQLModel, table=True)` con FK |
| Herencia Python | Sí (Paciente hereda métodos de Usuario) | No (pero tiene `usuario: Usuario = Relationship()`) |
| Consulta | JOIN implícito (SQLAlchemy) | `.usuario` explícito |
| SQLModel puro | ❌ No (usa feature de SQLAlchemy) | ✅ Sí |

**Ventaja colateral**: Ahora `Usuario`, `Paciente` y `Medico` son tablas independientes y consultables por separado. Se puede buscar un usuario por email sin hacer JOIN.

### ~🟡 R2: URL async/sync PostgreSQL (RESUELTO)~

Se usarán dos URLs en `.env`:
```
DATABASE_URL=postgresql+asyncpg://postgres:...@host:5432/postgres    ← para la app
DATABASE_URL_SYNC=postgresql://postgres:...@host:5432/postgres       ← para Alembic
```

### ~🟡 R3: Python 3.10+ (VERIFICADO)~

FastAPI 0.136.3 requiere Python ≥ 3.10 (drop de Python 3.9 desde v0.129). Recomendado: Python 3.11 o 3.12.

### ✅ ADR-004 actualizado

El ADR-004 (`joined-table-inheritance.md`) fue actualizado. La decisión ahora es **FK Simple (1:1)** — SQLModel puro con Usuario, Paciente y Medico como modelos separados unidos por ForeignKey + Relationship. No requiere crear un nuevo ADR.

---

## 6. Decisiones Arquitectónicas (Todas Resueltas)

| # | Pregunta | Decisión | Justificación |
|---|----------|----------|---------------|
| 1 | **¿Herencia joined o FK simple?** | **FK simple (1:1)** | SQLModel puro, sin trucos de SQLAlchemy. Una tabla Usuario con `tipo`, y Paciente/Medico con FK a Usuario. |
| 2 | **¿WebSocket para telemetría?** | **Sí** | `WS /ws/telemetria/{paciente_id}` en `routers/telemetria.py`. El frontend se suscribe y recibe telemetría en tiempo real. |
| 3 | **¿Token WearOS: JWT o string fijo?** | **JWT rotable** | Misma librería python-jose que para médicos. El dispositivo recibe un JWT al vincularse, con expiración. Al revocar, el token expira. |
| 4 | **¿Plan B si Supabase falla en demo?** | **No hay plan B** | Siempre Supabase. Si falla, se demuestra con capturas de pantalla y video grabado. Alternativa futura: Docker PostgreSQL local. |
| 5 | **¿Umbrales de riesgo fijos o dinámicos?** | **Configurables (JSON)** | Archivo `app/config/umbrales.json` con valores por defecto. El médico puede sobrescribirlos. |
| 6 | **¿Ventana de Evento configurable?** | **Sí, 5 min default** | Mismo archivo `umbrales.json`. Configurable por tipo de evento: anomalía crítica → ventana más corta, reporte periódico → ventana más larga. |

### Detalle de cada decisión

#### D1: FK simple (Herencia)

```python
# Así NO:
class Paciente(Usuario, table=True):   # joined table inheritance — no funciona limpio en SQLModel

# Así SÍ:
class Paciente(SQLModel, table=True):
    __tablename__ = "pacientes"
    id: int = Field(foreign_key="usuarios.id", primary_key=True)
    fechaNacimiento: date
    usuario: Usuario = Relationship()
```

El service que crea un paciente hace dos operaciones:
```python
def crear_paciente(db, data):
    usuario = Usuario(**data.usuario, tipo="paciente")
    db.add(usuario)
    db.commit()
    paciente = Paciente(id=usuario.id, fechaNacimiento=data.fechaNacimiento)
    db.add(paciente)
    db.commit()
    return paciente
```

#### D2: WebSocket

Endpoint en `routers/telemetria.py`:
```
WS /ws/telemetria/{paciente_id}
```

El frontend (dashboard médico) se conecta a este WebSocket para recibir telemetría en vivo. Cuando `telemetria_service` recibe y valida una telemetría, la envía por WebSocket a los suscriptores del paciente correspondiente.

```
[WearOS] → POST /telemetria → [Backend] → store + broadcast WebSocket → [Frontend]
```

#### D3: Token WearOS JWT

- El dispositivo se registra con `POST /dispositivos` y recibe un JWT con `sub=dispositivo_id`, `exp=30d`.
- Cada request de telemetría incluye `Authorization: Bearer <jwt>`.
- `revocarToken()` invalida el JWT (se agrega a una blacklist o se cambia el secret del dispositivo).
- Misma librería que la autenticación de médicos: `python-jose`.

#### D4: Sin plan B para Supabase

Riesgo aceptado. La demo depende de Supabase. Si falla, se muestra el video grabado. Para mitigar: tener Docker PostgreSQL local como respaldo (no configurado, pero documentado como mejora futura).

#### D5 + D6: Configuración de umbrales

Archivo `app/config/umbrales.json`:

```json
{
  "umbrales": {
    "fc_max": 120,
    "fc_min": 40,
    "spo2_min": 90,
    "oldpeak_max": 2.0
  },
  "ventana_evento_minutos": 5,
  "ventana_evento_anomalia_minutos": 1,
  "clasificacion": {
    "bajo": 0.3,
    "medio": 0.7
  }
}
```

- `bajo`: probabilidad < 0.3
- `medio`: 0.3 ≤ probabilidad < 0.7
- `alto`: probabilidad ≥ 0.7

`evaluarUmbrales()` lee este archivo y compara `valorAgregado` contra los umbrales. El médico puede sobrescribir umbrales por paciente (en ese caso, se almacenan como JSON en `Perfil` o en una tabla separada de configuración).

---

## 7. Arquitectura de Comunicación Completa

```
┌─────────────────────────────────────────────────────────────────────┐
│                       COMUNICACIÓN ENTRE MÓDULOS                    │
└─────────────────────────────────────────────────────────────────────┘

 FRONTEND (dashboard médico)
   │
   ├── REST ◀──▶ Backend  (CRUD pacientes, triajes, alertas, etc.)
   │
   └── WS ◀──── Backend  (/ws/telemetria/{paciente_id} — tiempo real)
               
 WEAROS
   │
   └── REST (JWT) ──▶ Backend  (POST /telemetria — datos crudos)

 n8n
   │
   ├── Webhook ◀── Backend  (cuando un Evento necesita orquestación)
   │
   └── Webhook ──▶ Backend  (cuando n8n completa un workflow)

 MICROSERVICE (Python)
   │
   └── HTTP ◀──── Backend  (httpx.AsyncClient — solicitar predicción)
```

---

## 8. WebSocket para Telemetría en Vivo

### Especificación

| Aspecto | Valor |
|---------|-------|
| Endpoint | `ws://host:8000/ws/telemetria/{paciente_id}` |
| Formato | JSON |
| Autenticación | Token JWT en query param: `?token=jwt...` |
| Mensajes | `{ "tipo": "telemetria", "fc": 72, "spo2": 98, "timestamp": "..." }` |
| Broadcast | Cada POST /telemetria válido se reenvía a los WS del paciente |
| Librería | `websockets` + Starlette WebSocket (incluido en FastAPI) |

### Flujo

```
1. Frontend se conecta: ws://localhost:8000/ws/telemetria/42?token=xxx
2. Backend verifica JWT, extrae paciente_id=42
3. Backend agrega la conexión a un mapa: { 42: [websocket_1, ...] }
4. WearOS envía: POST /telemetria { dispositivo_id, frecuenciaCardiaca, spo2 }
5. telemetria_service.valida() → True
6. Backend guarda en BD
7. Backend busca websockets suscritos al paciente_id del dispositivo
8. Backend envía por cada WS: { "fc": 72, "spo2": 98, "timestamp": "..." }
9. Frontend recibe y actualiza dashboard en tiempo real
```

---

## 9. Resumen de Archivos a Crear

| Capa | Archivos | Líneas estimadas |
|------|----------|-----------------|
| Core | 5 (`__init__`, `main.py`, `dependencies.py`, `settings.py`) | ~150 |
| Models | 7 (`__init__`, `usuario.py`, `perfil.py`, `triaje.py`, `alerta.py`, `patologia.py`, `dispositivo.py`, `enum.py`) | ~400 |
| Schemas | ~5 (request/response por entidad) | ~200 |
| Routers | 11 (incluye WebSocket) | ~550 |
| Services | 8 | ~600 |
| Database | 2 (`database.py`, `security.py`) | ~100 |
| Config | 1 (`umbrales.json`) | ~30 |
| Tests | ~8 + conftest.py | ~400 |
| Infra | `requirements.txt`, `pyproject.toml`, `Dockerfile` | ~30 |
| **Total** | **~48 archivos** | **~2,460 líneas** |

---

## 10. Estado de los ADRs

| ADR | Estado | Acción |
|-----|--------|--------|
| ADR-001: FastAPI vs Django | ✅ Vigente | — |
| ADR-002: SQLModel vs SQLAlchemy | ✅ Vigente | — |
| ADR-003: SQLite vs PostgreSQL | ✅ Vigente (con Supabase) | — |
| ADR-004: FK Simple (1:1) para Usuario→Paciente/Medico | ✅ **Actualizado** | Joined table → FK simple |
| ADR-005: Services vs Model Methods | ✅ Vigente | — |
| ADR-006: HTTP Microservice Communication | ✅ Vigente | — |
| ADR-007: SimPy Demo Simulation | ✅ Vigente | — |
| **ADR-008 (nuevo)** | **⬜ Pendiente** | Crear: "FK simple en lugar de herencia de tablas" |
