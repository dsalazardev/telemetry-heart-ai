## Why

El diagrama UML en Lucidchart refleja el estado **pre-refactor** del dominio (versión original), mientras que el diagrama Mermaid en `Documents/Diagrama UML.md` ya fue actualizado a la **v2.0** con correcciones estructurales críticas (herencia de Usuario, Evaluacion como snapshot, Evento como agregador, Alerta como entidad, etc.). Tener dos diagramas divergentes genera confianza para agentes autónomos y desarrolladores. Esta actualización sincroniza el Lucid con el Mermaid v2.0 para que ambos sean el mismo documento fuente.

## What Changes

- Crear clase `Usuario` como base de herencia para Paciente y Medico
- Reestructurar `Perfil` para que solo contenga datos demográficos estables (mover Cleveland fields a nueva clase `Lectura`)
- Crear clase `Evaluacion` como snapshot clínico que agrupa `Lectura` + `Prediccion`
- Crear clase `Lectura` con los 13 atributos del dataset Cleveland
- Desacoplar `Prediccion` de parámetros específicos de AG (reemplazar por `metadataTecnica: JSON`)
- Crear clase `Alerta` como entidad de primera clase con ciclo de vida completo
- Crear clase `Evento` como agregador entre Telemetria y Workflow
- Crear clase `Documento` para el RAG del microservicio
- Corregir relación `Telemetria → Workflow` (1:1 directo) a `Telemetria → Evento → Workflow`
- Agregar estereotipos `<<backend>>`, `<<microservice>>`, `<<interface>>` a todas las clases
- Limpiar placeholders UML en la interfaz Workflow
- Eliminar `generacionesAg`, `recallObtenido`, `cromosomaOptimo` de Prediccion
- Eliminar `turno` de Medico, `createdAt` de Paciente
- Ajustar multiplicidades y nombres de métodos para coincidir con Mermaid v2.0

## Capabilities

### New Capabilities
- `lucid-diagram-sync`: mantener el diagrama Lucidchart sincronizado con el diagrama Mermaid de referencia

### Modified Capabilities

Ninguna — es la primera sincronización del Lucid.

## Impact

- **Diagrama Lucidchart**: se modifican 8 clases existentes y se crean 5 nuevas
- **Documents/Diagrama UML.md**: sin cambios (es el estado deseado de referencia)
- **Agentes autónomos**: el Lucid será implementable sin necesidad de leer ambas versiones y discernir diferencias
