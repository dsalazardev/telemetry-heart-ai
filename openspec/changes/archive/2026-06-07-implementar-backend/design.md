## Context

El proyecto `Project/backend/` solo contiene documentación (`AGENTS.md`, `README.md`, 7 ADRs, `.env` con credenciales Supabase) y cero líneas de código. El backend es el núcleo del ecosistema de triaje cardiovascular IoT: debe recibir telemetría desde dispositivos WearOS, persistir datos clínicos en PostgreSQL, exponer API REST para el dashboard médico, y comunicarse con el microservicio de IA para predicción de riesgo. La entrega académica requiere una demo de 10 min + 5 min Q&A con máximo 30 pacientes simulados.

## Goals / Non-Goals

**Goals:**
- Proyecto base FastAPI 0.136.3 + SQLModel 0.0.37 con arquitectura limpia (routers → services → models).
- 12 modelos SQLModel mapeados desde el diagrama UML con FK simple (NO herencia de tablas).
- Auth JWT para médicos y tokens rotables JWT para dispositivos WearOS.
- WebSocket `/ws/telemetria/{paciente_id}` para broadcast de telemetría en tiempo real.
- Cliente HTTP async (`httpx.AsyncClient`) para comunicación con el microservicio de IA.
- Configuración de umbrales de riesgo y ventanas de evento vía `app/config/umbrales.json`.
- Migraciones Alembic funcionando contra PostgreSQL en Supabase (async para app, sync para Alembic).
- Suite de tests con pytest (~8 archivos).
- Demo con SimPy usando datos del dataset Cleveland.

**Non-Goals:**
- No se implementa el microservicio de IA (LangChain, ML, metaheurísticas) — ese es otro módulo.
- No se implementa el frontend (dashboard médico) — solo se exponen endpoints REST y WebSocket.
- No se configura infraestructura de producción (Docker compose, deploy, CI/CD).
- No se usa herencia de tablas (joined table inheritance) — se descartó por incompatibilidad con SQLModel.
- No hay plan B si Supabase falla en demo — se acepta el riesgo y se mitiga con video grabado.

## Decisions

### D1: FK Simple (1:1) para Usuario → Paciente / Medico
- **Decisión**: Usuario, Paciente y Medico son tablas independientes. Paciente y Medico tienen `id` como PK y FK a `usuarios.id`. En Python NO heredan de Usuario — usan `Relationship()`.
- **Rationale**: SQLModel no soporta herencia de tablas de forma limpia. La sintaxis `class Paciente(Usuario, table=True)` mezcla SQLAlchemy y SQLModel y genera errores. FK simple es SQLModel puro, funciona, se entiende, y se defiende en Q&A.
- **Alternativas consideradas**: Joined table inheritance (SQLAlchemy) — descartado porque no es SQLModel puro y genera problemas de mapeo.

### D2: Dos URLs de PostgreSQL (Async + Sync)
- **Decisión**: `DATABASE_URL_ASYNC` (`postgresql+asyncpg://`) para la app FastAPI, `DATABASE_URL` (`postgresql://`) para Alembic.
- **Rationale**: FastAPI requiere driver async (`asyncpg`) para operaciones no bloqueantes. Alembic requiere driver síncrono (`psycopg2-binary`) para migraciones. Dos URLs permiten que cada herramienta use el driver correcto sin hacks.
- **Alternativas consideradas**: Usar solo sync y envolver en `run_in_executor` — descartado por complejidad innecesaria y pérdida de beneficios async.

### D3: WebSocket para Telemetría en Vivo
- **Decisión**: Endpoint `WS /ws/telemetria/{paciente_id}` con autenticación JWT via query param `?token=...`.
- **Rationale**: El frontend necesita actualizar el dashboard en tiempo real sin polling. WebSocket es nativo en FastAPI (Starlette) y requiere solo el paquete `websockets`. Cada POST /telemetria válido se reenvía a los suscriptores del paciente.
- **Alternativas consideradas**: Server-Sent Events (SSE) — descartado porque WebSocket permite comunicación bidireccional futura (ej: enviar comandos al dispositivo).

### D4: Token WearOS como JWT Rotable
- **Decisión**: El dispositivo recibe un JWT al vincularse (`POST /dispositivos`) con `sub=dispositivo_id` y `exp=30d`. Revocación invalida el JWT (blacklist o cambio de secret).
- **Rationale**: Reutiliza la misma librería (`python-jose`) que la auth de médicos. JWT es stateless y escala bien. Un string fijo sería inseguro (no expira, no se puede revocar sin cambiar código).
- **Alternativas consideradas**: Token string fijo almacenado en BD — descartado por falta de expiración y dificultad de revocación.

### D5: Umbrales Configurables vía JSON
- **Decisión**: Archivo `app/config/umbrales.json` con valores por defecto (bajo < 0.3, medio < 0.7, alto ≥ 0.7). Ventana de evento: 5 min default, configurable por tipo.
- **Rationale**: Los umbrales fijos son rígidos para un entorno clínico donde cada paciente tiene necesidades distintas. JSON permite modificar sin redeploy. El médico puede sobrescribir por paciente (almacenado en `Perfil` o tabla de configuración).
- **Alternativas consideradas**: Hardcodear en Python — descartado por inflexibilidad.

### D6: Services Separados de Modelos
- **Decisión**: Lógica de negocio en `services/`, modelos SQLModel puros en `models/`.
- **Rationale**: Separa responsabilidades. Los modelos definen el esquema de BD. Los services contienen la lógica de negocio (ej: `notificarTelegram()`, `escalarUrgencia()`). Facilita testing unitario.
- **Alternativas consideradas**: Métodos de instancia en modelos (Active Record) — descartado porque SQLModel no lo promueve y mezcla capas.

### D7: Python ≥ 3.10
- **Decisión**: Requerir Python 3.10, 3.11 o 3.12. No soportar 3.9.
- **Rationale**: FastAPI 0.129.0+ dropped Python 3.9. FastAPI 0.136.3 requiere Python ≥ 3.10. Usar una versión moderna asegura compatibilidad y acceso a features como `match/case` y mejoras en `asyncio`.
- **Alternativas consideradas**: Usar FastAPI 0.128 (soporta 3.9) — descartado porque perdemos bug fixes y mejoras de performance.

## Risks / Trade-offs

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| **Supabase no disponible en demo** | Alto — sin BD no hay persistencia | Aceptado. Si falla, se muestra video grabado. Docker PostgreSQL local documentado como mejora futura. |
| **Herencia FK simple requiere JOINs manuales** | Medio — más verbose que herencia automática | Mitigado. Los services encapsulan los JOINs. El patrón es defensible en Q&A. |
| **WebSocket con JWT en query param puede filtrarse en logs** | Medio — el token aparece en URLs | Mitigado. Tokens de corta duración (30 min para frontend, 30d para dispositivos). En prod se usaría header `Sec-WebSocket-Protocol` o cookie. |
| **asyncpg + psycopg2 duplican dependencias** | Bajo — aumenta tamaño de imagen | Aceptado. Es el patrón estándar en FastAPI + Alembic. |
| **12 modelos en una sola fase de migración** | Medio — riesgo de errores en la primera migración | Mitigado. Se crean en orden por dependencias de FK (Fase 0→1→2→...). Alembic revision autogenerada y revisada manualmente. |

## Migration Plan

No aplica migración de datos (proyecto nuevo). Los pasos de deploy son:
1. Instalar dependencias: `pip install -r requirements.txt`
2. Verificar `.env` con `DATABASE_URL` y `DATABASE_URL_ASYNC`
3. Crear migración inicial: `alembic revision --autogenerate -m "init"`
4. Aplicar migración: `alembic upgrade head`
5. Verificar tablas en Supabase Dashboard
6. Iniciar app: `uvicorn app.main:app --reload`
7. Ejecutar tests: `pytest`

Rollback: `alembic downgrade -1` (revertir última migración).

## Open Questions

- *(ninguno — todas las decisiones arquitectónicas fueron resueltas en la fase de exploración)*
