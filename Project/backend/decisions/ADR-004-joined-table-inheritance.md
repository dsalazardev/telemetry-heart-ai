# ADR-004: Representación de Herencia UML en Base de Datos

**Fecha:** 2026-06-07
**Estado:** Actualizado — FK simple (1:1) reemplaza joined table inheritance

## Contexto

El diagrama UML define herencia:
```
Usuario <|-- Paciente
Usuario <|-- Medico
```

En SQLModel no hay soporte nativo para herencia de tablas. Necesitamos representar esta relación en la base de datos manteniendo:
- Integridad referencial
- Campos compartidos sin duplicación
- SQLModel puro (sin mezclar SQLAlchemy inheritance)

## Opciones Consideradas

### Opción 1: Single Table Inheritance
- Una sola tabla `usuarios` con todos los campos (Paciente + Medico + Usuario)
- Columna `tipo` para discriminar
- Muchos campos nulos (Paciente no tiene licencia, Medico no tiene fechaNacimiento)
- Simple pero desnormalizado

### Opción 2: Joined Table Inheritance ← **DESCARTADA**
- Una tabla `usuarios` con campos comunes
- Una tabla `pacientes` y `medicos` con FK + herencia SQLAlchemy
- Requiere mezclar SQLModel con SQLAlchemy inheritance API
- El código se vuelve críptico y difícil de mantener

### Opción 3: FK Simple (1:1) ← **ELEGIDA**
- `Usuario` es una tabla independiente con `tipo: str`
- `Paciente` tiene FK 1:1 a Usuario
- `Medico` tiene FK 1:1 a Usuario
- SQLModel puro, sin herencia de tablas
- Se pierde la herencia de clases Python, pero la BD está normalizada

## Decisión

**FK Simple (1:1)** — Usuario, Paciente y Medico como modelos SQLModel separados, unidos por ForeignKey + Relationship.

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

## Fundamentos

1. **SQLModel puro**: No mezcla con SQLAlchemy inheritance. Todo es SQLModel estándar.
2. **Sin campos nulos**: Cada tabla solo tiene los campos que necesita.
3. **Integridad referencial**: FK garantiza que Paciente/Medico existen como Usuario.
4. **Polimorfismo vía service**: En el service se consulta Usuario + Paciente/Medico por separado y se arma el objeto completo.

## Consecuencias

- Positivas: SQLModel puro, sin trucos, fácil de mantener
- Positivas: Código claro y defendible en Q&A
- Negativas: Se pierde la herencia de clases Python (Paciente ya no "es un" Usuario en código)
- Negativas: Dos consultas para obtener datos completos (Usuario + Paciente/Medico)

## Riesgos

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| Dos consultas en vez de JOIN | Baja | El service puede hacerlas en paralelo con asyncio y combinarlas |
| Confusión en Q&A "¿por qué no hereda?" | Media | "SQLModel no soporta herencia de tablas. Usamos composición con FK 1:1 que es más limpio y no requiere mezclar tecnologías" |

## Referencias

- [SQLModel Relationship](https://sqlmodel.tiangolo.com/tutorial/fastapi/relationships/)
- [ADR-002: SQLModel vs SQLAlchemy](decisions/ADR-002-sqlmodel-vs-sqlalchemy.md)
