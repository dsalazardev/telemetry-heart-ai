# ADR-004: Joined Table Inheritance para Usuario → Paciente / Medico

**Fecha:** 2026-06-07
**Estado:** Aceptado

## Contexto

El diagrama UML define herencia:
```
Usuario <|-- Paciente
Usuario <|-- Medico
```

En SQLModel no hay soporte nativo para herencia de tablas. Necesitamos representar esta relación en la base de datos manteniendo:
- Integridad referencial
- Campos compartidos sin duplicación
- Consultas polimórficas (buscar Usuario por ID sin saber si es Paciente o Medico)

## Opciones Consideradas

### Opción 1: Single Table Inheritance
- Una sola tabla `usuarios` con todos los campos (Paciente + Medico + Usuario)
- Columna `tipo` para discriminar
- Muchos campos nulos (Paciente no tiene licencia, Medico no tiene fechaNacimiento)
- Simple pero desnormalizado

### Opción 2: Joined Table Inheritance
- Una tabla `usuarios` con campos comunes
- Una tabla `pacientes` con FK a usuarios + campos específicos
- Una tabla `medicos` con FK a usuarios + campos específicos
- JOIN para obtener datos completos
- Normalizado, sin campos nulos

### Opción 3: Concrete Table Inheritance
- Tablas separadas sin tabla base
- Duplicación de columnas comunes
- Sin polimorfismo

## Decisión

**Joined Table Inheritance** — una tabla por clase, unidas por ID.

## Fundamentos

1. **Sin datos nulos**: Cada tabla solo tiene los campos que necesita
2. **Integridad referencial**: FK garantiza que un Paciente existe como Usuario
3. **Polimorfismo**: Se puede consultar `Usuario` y saber si es paciente o médico por la columna `tipo`
4. **Escape SQLModel**: La herencia no funciona en SQLModel puro, pero se implementa con SQLAlchemy query API y SQLModel para las tablas base

## Consecuencias

- Positivas: Modelo normalizado, sin duplicación, consultas eficientes
- Negativas: Requiere JOIN para obtener datos completos (costo mínimo)
- Negativas: No se puede usar SQLModel puro para la herencia — se mezcla con SQLAlchemy

## Riesgos

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| Complejidad extra por mezclar SQLModel + SQLAlchemy inheritance | Media | Documentar el patrón en el código y en AGENTS.md |
| Confusión en Q&A sobre por qué no es SQLModel puro | Media | "SQLModel no soporta herencia. Usamos SQLAlchemy inheritance que es el motor debajo de SQLModel" |

## Ejemplo de Implementación

```python
from sqlmodel import SQLModel, Field

class UsuarioBase(SQLModel):
    documento: str = Field(index=True, unique=True)
    nombres: str
    apellidos: str
    correo: str = Field(index=True, unique=True)
    password: str
    telefono: str
    activo: bool = True

class Usuario(UsuarioBase, table=True):
    __tablename__ = "usuarios"
    id: int = Field(primary_key=True)
    tipo: str = Field(index=True)  # "paciente" | "medico"

class Paciente(UsuarioBase, table=True):
    __tablename__ = "pacientes"
    id: int = Field(foreign_key="usuarios.id", primary_key=True)
    fechaNacimiento: date
```

## Referencias

- [SQLAlchemy Joined Table Inheritance](https://docs.sqlalchemy.org/en/20/orm/inheritance.html#joined-table-inheritance)
- ADR-002: SQLModel vs SQLAlchemy
