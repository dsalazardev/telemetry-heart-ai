## 1. Fase 0 — Proyecto Base (~30 min)

- [x] 1.1 Crear `Project/backend/requirements.txt` con todas las dependencias (FastAPI 0.136.3, SQLModel 0.0.37, Pydantic 2.12.2, Alembic, python-jose, passlib[bcrypt], pytest, httpx, NumPy, asyncpg, pydantic-settings, uvicorn[standard], psycopg2-binary, websockets)
- [x] 1.2 Crear `Project/backend/app/__init__.py` y `Project/backend/app/main.py` (FastAPI app vacía con lifespan)
- [x] 1.3 Crear `Project/backend/app/core/settings.py` (pydantic-settings con `DATABASE_URL`, `DATABASE_URL_ASYNC`, `MICROSERVICE_URL`)
- [x] 1.4 Crear `Project/backend/app/core/database.py` (engine async con `create_async_engine` + `asyncpg`, session factory `AsyncSession`)
- [x] 1.5 Crear `Project/backend/app/dependencies.py` (`get_db` que provee `AsyncSession`)
- [x] 1.6 Inicializar Alembic: `alembic init alembic/` y adaptar `alembic/env.py` para usar `DATABASE_URL` (sync) desde `Settings`
- [x] 1.7 Verificar: `uvicorn app.main:app --reload` responde `GET /` con `{ }`

## 2. Fase 1 — Modelos + Schemas + Config (~2h)

- [x] 2.1 Crear `Project/backend/app/models/__init__.py`
- [x] 2.2 Crear `Project/backend/app/models/enum.py` (Enums: `NivelUrgencia`, `TipoEvento`, `EstadoProcesamiento`)
- [x] 2.3 Crear `Project/backend/app/models/usuario.py` (`Usuario`, `Paciente`, `Medico` con FK simple 1:1, `Relationship()`)
- [x] 2.4 Crear `Project/backend/app/models/perfil.py` (`Perfil` con FK a `pacientes`)
- [x] 2.5 Crear `Project/backend/app/models/patologia.py` (`Patologia`, `Historial` con FKs)
- [x] 2.6 Crear `Project/backend/app/models/dispositivo.py` (`Dispositivo`, `Telemetria`, `Evento` con FKs y `valorAgregado: dict = Field(sa_type=JSON)`)
- [x] 2.7 Crear `Project/backend/app/models/triaje.py` (`Triaje`, `Alerta`, `Log` con FKs y `diagnosticoConfirmado: bool | None`)
- [x] 2.8 Crear `Project/backend/app/config/umbrales.json` (umbrales fc, spo2, oldpeak, ventana_evento, clasificación bajo/medio/alto)
- [x] 2.9 Crear schemas Pydantic (~5 archivos): `app/schemas/__init__.py`, `usuario.py`, `triaje.py`, `alerta.py`, `dispositivo.py`
- [x] 2.10 Generar primera migración Alembic: `alembic revision --autogenerate -m "init"` y revisar manualmente
- [x] 2.11 Aplicar migración: `alembic upgrade head` y verificar tablas en Supabase Dashboard

## 3. Fase 2 — Core + Auth (~1.5h)

- [x] 3.1 Crear `Project/backend/app/core/security.py` (JWT create/verify con `python-jose`, password hash/verify con `bcrypt`)
- [x] 3.2 Crear `Project/backend/app/services/auth_service.py` (login, refresh, verificación de tokens de médicos y dispositivos)
- [x] 3.3 Crear `Project/backend/app/routers/auth.py` (`POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`)
- [x] 3.4 Crear `Project/backend/app/dependencies.py` + `get_current_user()` (verificar JWT en `Authorization: Bearer`)
- [x] 3.5 Crear `Project/backend/tests/conftest.py` (fixtures: test db SQLite en memoria, async client, auth headers)
- [x] 3.6 Crear `Project/backend/tests/test_auth.py` (tests de login exitoso, login fallido, refresh)

## 4. Fase 3 — CRUD Pacientes + Médicos (~2h)

- [x] 4.1 Crear `Project/backend/app/services/paciente_service.py` (crear paciente con usuario, listar, actualizar, eliminar)
- [x] 4.2 Crear `Project/backend/app/routers/pacientes.py` (`GET/POST /pacientes`, `GET/PUT/DELETE /pacientes/{id}`, `GET/PUT /pacientes/{id}/perfil`)
- [x] 4.3 Crear `Project/backend/app/routers/medicos.py` (`GET/POST /medicos`, `GET/PUT/DELETE /medicos/{id}`)
- [x] 4.4 Crear `Project/backend/app/routers/patologias.py` (`GET/POST /patologias`)
- [x] 4.5 Crear `Project/backend/app/routers/historiales.py` (rutas anidadas en `/pacientes/{id}/historiales`)
- [x] 4.6 Crear `Project/backend/tests/test_pacientes.py` (CRUD paciente, perfil, historiales)
- [x] 4.7 Verificar FK simple: crear paciente → usuario + paciente vinculados correctamente en BD

## 5. Fase 4 — Triaje + Alertas (~2h)

- [x] 5.1 Crear `Project/backend/app/services/triaje_service.py` (crear triaje, listar pendientes, atender, notificarTelegram, escalarUrgencia, registrar logs)
- [x] 5.2 Crear `Project/backend/app/routers/triajes.py` (`GET/POST /triajes`, `GET /triajes/pendientes`, `PUT /triajes/{id}/atender`, `GET /triajes/{id}/logs`)
- [x] 5.3 Crear `Project/backend/app/services/alerta_service.py` (emitir, marcarLeida, asignarMedico, atender)
- [x] 5.4 Crear `Project/backend/app/routers/alertas.py` (`GET /alertas`, `PUT /alertas/{id}/leer`, `PUT /alertas/{id}/asignar`, `PUT /alertas/{id}/atender`)
- [x] 5.5 Crear `Project/backend/tests/test_triajes.py` (crear triaje, listar pendientes, atender, logs)
- [x] 5.6 Crear `Project/backend/tests/test_alertas.py` (emitir, leer, asignar, atender, filtros)

## 6. Fase 5 — Telemetría + Eventos + WebSocket (~2.5h)

- [x] 6.1 Crear `Project/backend/app/services/telemetria_service.py` (validar rangos, almacenar, enriquecerConLab)
- [x] 6.2 Crear `Project/backend/app/services/evento_service.py` (agregar a evento activo o crear nuevo, evaluarUmbrales, llamar microservicio)
- [x] 6.3 Crear `Project/backend/app/routers/telemetria.py` (`POST /telemetria` desde WearOS + `WS /ws/telemetria/{paciente_id}`)
- [x] 6.4 Implementar broadcast WebSocket: al recibir POST /telemetria válido, reenviar JSON a websockets suscritos del paciente
- [x] 6.5 Implementar autenticación WebSocket via query param `?token=...` y rechazar sin token (código 1008)
- [x] 6.6 Crear `Project/backend/app/routers/eventos.py` (`GET /eventos`, `POST /eventos/{id}/evaluar`)
- [x] 6.7 Crear `Project/backend/tests/test_telemetria.py` (POST válido, POST sin token, validación rangos)
- [x] 6.8 Crear `Project/backend/tests/test_eventos.py` (crear evento, evaluar umbrales, agregar telemetrías)
- [x] 6.9 Crear `Project/backend/tests/test_websocket.py` (conexión exitosa, conexión sin token, broadcast de mensaje)

## 7. Fase 6 — Comunicación Microservicio (~1h)

- [x] 7.1 Crear `Project/backend/app/services/microservice_client.py` (`httpx.AsyncClient` con base_url desde `Settings.MICROSERVICE_URL`)
- [x] 7.2 Implementar `solicitar_prediccion(datos_lectura: dict) → dict` con timeout de 10 segundos
- [x] 7.3 Integrar llamado a microservicio en `evento_service.evaluarUmbrales()` (flujo completo: evento → predicción → triaje → alerta)
- [x] 7.4 Crear `Project/backend/tests/test_microservice_client.py` (mock de httpx, timeout, respuesta válida, error de conexión)
- [x] 7.5 Verificar que `evento_service` maneja timeout del microservicio (`estadoProcesamiento = "timeout_microservicio"`)

## 8. Fase 7 — Demo + SimPy + Utils (~1h)

- [x] 8.1 Crear `Project/backend/app/utils/estadisticas.py` (SimPy simulation con datos del dataset Cleveland: crear proceso de paciente, triaje, alerta)
- [x] 8.2 Crear script de demo (`scripts/demo.py` o similar) que simula 30 pacientes con datos reales del CSV
- [x] 8.3 Verificar que el script de demo corre sin errores y genera triajes/alertas en BD
- [x] 8.4 Actualizar `Project/backend/AGENTS.md` si cambió algo del stack o estructura durante la implementación
