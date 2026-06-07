# ADR-002: SQLModel vs SQLAlchemy

**Fecha:** 2026-06-07
**Estado:** Aceptado

## Contexto

El backend necesita un ORM para persistir las 12 clases `<<backend>>` del diagrama UML. Los requisitos:
- Tipado fuerte (Python type hints)
- Integración con FastAPI y Pydantic
- Soporte para migraciones
- Herencia de tablas (Usuario → Paciente/Medico)
- Relaciones entre entidades

## Opciones Consideradas

### Opción 1: SQLAlchemy 2.0 + Pydantic v2
- ORM más maduro del ecosistema Python
- Soporte nativo de herencia (joined, single, concrete)
- Requiere mantener modelos de BD + schemas Pydantic por separado
- Más código boilerplate

### Opción 2: SQLModel
- Unifica modelos de BD y schemas Pydantic (una sola clase)
- Construido sobre SQLAlchemy 2.0 + Pydantic v2
- Menos código, menos archivos
- Auto-generación de schemas request/response desde el modelo
- Integración directa con FastAPI (dependency injection)

### Opción 3: Django ORM
- Solo viable si usáramos Django (descartado en ADR-001)

## Decisión

**SQLModel v0.0.37**

## Fundamentos

1. **Unificación**: Un solo archivo `models/paciente.py` define la tabla, el schema de creación, el schema de respuesta y el schema de actualización. Con SQLAlchemy serían 4 archivos.
2. **Menos archivos**: Para 12 clases `<<backend>>`, la reducción es de ~48 archivos a ~12. En un proyecto académico, eso importa.
3. **Integración FastAPI**: `session.exec(select(Paciente))` es más limpio que `session.query(Paciente).all()`.
4. **Escape hatch**: Si SQLModel no soporta algo, se puede usar SQLAlchemy directamente. Es una capa delgada sobre SQLAlchemy.

## Consecuencias

- Positivas: Código más conciso, menos archivos que mantener, mismos tipos para BD y API
- Negativas: SQLModel no soporta herencia de tablas nativamente → se usa joined table inheritance de SQLAlchemy
- Negativas: SQLModel es menos maduro (v0.0.37) — bugs potenciales en casos límite

## Riesgos

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| Bug en SQLModel | Baja | El escape hatch a SQLAlchemy siempre está disponible |
| Herencia no soportada | Alta | Ya identificado. Se usa joined table inheritance de SQLAlchemy (ver ADR-004) |

## Referencias

- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- ctx7: `/websites/sqlmodel_tiangolo` — v0.0.37
