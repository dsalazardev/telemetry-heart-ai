# ADR-003: SQLite vs PostgreSQL

**Fecha:** 2026-06-07
**Estado:** Aceptado (Actualizado: SQLite → PostgreSQL remoto)

## Contexto

El backend necesita una base de datos relacional para persistir las entidades del dominio. El sistema maneja:
- ~30 pacientes en simulación
- ~18 tablas (herencia incluida)
- Telemetría cada 5 minutos por paciente (~8,640 registros/día)
- Triajes, alertas, logs, historiales clínicos
- Una demo en vivo de 10 minutos + 5 min Q&A
- El equipo ya dispone de un servidor PostgreSQL remoto (Supabase)

## Opciones Consideradas

### Opción 1: PostgreSQL (Supabase) ← **ELEGIDA**
Base de datos cliente-servidor gestionada en la nube.

**Ventajas:**
- Relacional ACID completo — ideal para el dominio clínico con 18 tablas relacionadas
- Consultas JOIN nativas (Paciente → Triaje → Log → Medico en una sola query)
- JSON fields nativos (jsonb para valorAgregado, metadataTecnica, importanciaVariables)
- Sin riesgo de lock de escritura (conexiones concurrentes reales)
- Accesible desde cualquier lugar (el equipo no depende de un archivo local)
- Supabase: capa gratuita generosa (500 MB, respaldo automático)
- Integridad referencial real (FK, NOT NULL, CASCADE)

**Desventajas:**
- Requiere conexión a internet para funcionar
- Latencia de red (~10-50 ms vs 0 ms de SQLite)
- Dependencia del servicio externo

### Opción 2: SQLite
Base de datos embebida, sin servidor, un solo archivo.

**Ventajas:** Cero configuración, portátil, sin internet.
**Desventaja principal:** No accesible desde múltiples máquinas, riesgo de pérdida del archivo local.

Descartada porque el equipo prefiere una BD remota accesible desde cualquier máquina, con respaldo automático y sin riesgo de pérdida de datos locales.

### Opción 3: MongoDB Atlas
Base de datos NoSQL documental.

Descartada porque el dominio es predominantemente relacional (18 tablas, 18 relaciones). Las relaciones clínicas (Paciente → Triaje → Medico → Log) requieren JOINs e integridad referencial que MongoDB no ofrece nativamente.

## Decisión

**PostgreSQL en Supabase.** Usar SQLModel + Alembic.

```python
# Configuración en core/settings.py
DATABASE_URL = "postgresql://postgres:pXHRIGfzmh4uBbfP@db.haoaibtgrzljlwxeocom.supabase.co:5432/postgres"
```

**Credenciales del servidor:**
| Campo | Valor |
|-------|-------|
| Host | db.haoaibtgrzljlwxeocom.supabase.co |
| Port | 5432 |
| Database | postgres |
| User | postgres |
| Password | pXHRIGfzmh4uBbfP |

**IMPORTANTE:** La contraseña debe ir en `.env`, NUNCA en código fuente. Usar `python-dotenv`:

```python
# settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:***@db.haoaibtgrzljlwxeocom.supabase.co:5432/postgres"
    
    class Config:
        env_file = ".env"
```

## Consecuencias

**Positivas:**
- Integridad referencial real (FK, restricciones, ON DELETE CASCADE)
- Consultas complejas con JOINs nativos (una query vs múltiples viajes en NoSQL)
- Acceso remoto desde cualquier máquina del equipo
- Supabase: respaldo automático, sin pérdida de datos
- SQLModel + Alembic funcionan igual que con SQLite (solo cambia la URL)
- JSON nativo con jsonb para campos semiestructurados

**Negativas:**
- Requiere internet para la demo (plan B: hotspot o respaldo local)
- Latencia adicional (~10-50 ms por consulta)
- Las credenciales deben manejarse con .env

## Riesgos

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| Sin internet en la presentación | Media | Tener plan B: exportar a SQLite local con Alembic antes de la demo, o llevar hotspot |
| Credenciales expuestas en Git | Alta | `.env` en `.gitignore`, NUNCA hardcodear la contraseña |
| Límite Supabase gratis (500 MB) | Baja | 18 tablas con ~30 pacientes no llegan ni a 10 MB |
| Latencia ralentiza la demo | Baja | Supabase us-east-1, ~50ms, imperceptible en interfaz de usuario |

## Referencias

- [Supabase PostgreSQL Docs](https://supabase.com/docs/guides/database)
- [SQLModel + PostgreSQL](https://sqlmodel.tiangolo.com/advanced/)
- [Alembic with PostgreSQL](https://alembic.sqlalchemy.org/en/latest/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
