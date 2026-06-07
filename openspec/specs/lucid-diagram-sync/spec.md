# lucid-diagram-sync Specification

## Purpose
TBD - created by archiving change actualizar-diagrama-lucid. Update Purpose after archive.
## Requirements
### Requirement: Diagrama Lucidchart sincronizado con Mermaid v2.0

El diagrama Lucidchart SHALL reflejar exactamente el mismo contenido que el diagrama Mermaid en `Documents/Diagrama UML.md` en cuanto a clases, atributos, métodos, relaciones, multiplicidades y estereotipos.

#### Scenario: Coincidencia de clases existentes
- **WHEN** se comparan las clases del Lucidchart con las del Mermaid
- **THEN** cada clase que existe en ambos diagramas SHALL tener exactamente los mismos atributos y métodos

#### Scenario: Coincidencia de nuevas clases
- **WHEN** se comparan las clases del Lucidchart con las del Mermaid
- **THEN** el Lucidchart SHALL contener las 6 clases nuevas del Mermaid v2.0 (Usuario, Evaluacion, Lectura, Alerta, Evento, Documento)

#### Scenario: Coincidencia de relaciones
- **WHEN** se comparan las relaciones del Lucidchart con las del Mermaid
- **THEN** cada relación SHALL tener el mismo tipo, origen, destino y multiplicidades

### Requirement: Usuario como base de herencia

El Lucidchart SHALL mostrar la clase Usuario con sus atributos (documento, nombres, apellidos, telefono, activo) y las relaciones de herencia hacia Paciente y Medico.

#### Scenario: Herencia de Usuario
- **WHEN** se inspecciona el diagrama Lucidchart
- **THEN** Paciente SHALL heredar de Usuario (triángulo vacío en la línea)
- **THEN** Medico SHALL heredar de Usuario (triángulo vacío en la línea)

### Requirement: Perfil reestructurado

El Lucidchart SHALL reflejar la nueva estructura de Perfil que solo contiene datos demográficos estables (edad, sexo, tipoSangre, alergias).

#### Scenario: Perfil sin Cleveland fields
- **WHEN** se inspecciona la clase Perfil en el Lucidchart
- **THEN** NO SHALL contener los campos cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal
- **THEN** NO SHALL contener puntuacionIa, origenDatos, timestampEvaluacion
- **THEN** NO SHALL tener relación con Prediccion

### Requirement: Evaluacion como Aggregate Root

El Lucidchart SHALL mostrar Evaluacion como clase del microservicio con relación 1:1 a Lectura y 1:1 a Prediccion.

#### Scenario: Evaluacion correcta
- **WHEN** se inspecciona la clase Evaluacion
- **THEN** SHALL tener atributos: _id, fechaEvaluacion, origenDatos
- **THEN** SHALL tener relación 1:1 con Lectura
- **THEN** SHALL tener relación 1:1 con Prediccion

### Requirement: Prediccion desacoplada de AG

El Lucidchart SHALL reflejar Prediccion sin parámetros específicos de Algoritmo Genético.

#### Scenario: Prediccion sin AG params
- **WHEN** se inspecciona la clase Prediccion
- **THEN** NO SHALL contener generacionesAg, recallObtenido, cromosomaOptimo
- **THEN** SHALL contener metadataTecnica: JSON

### Requirement: Telemetria con Evento como agregador

El Lucidchart SHALL reflejar la relación Telemetria → Evento → Workflow en lugar de Telemetria → Workflow directo.

#### Scenario: Flujo Telemetria corregido
- **WHEN** se inspecciona la clase Telemetria
- **THEN** NO SHALL tener relación directa con Workflow
- **THEN** SHALL tener relación 1:* con Evento
- **WHEN** se inspecciona la clase Evento
- **THEN** SHALL tener relación 1:1 con Workflow

### Requirement: Alerta como entidad de primera clase

El Lucidchart SHALL mostrar Alerta como clase independiente con ciclo de vida completo.

#### Scenario: Alerta completa
- **WHEN** se inspecciona la clase Alerta
- **THEN** SHALL tener atributos: _id, tipo, mensaje, leida, atendida, fechaEmision, fechaAtencion
- **THEN** SHALL tener métodos: marcarLeida(), asignarMedico()
- **THEN** SHALL tener relación con Paciente (1:*), Medico (1:*), Triaje (0..1:1)

### Requirement: Esterotipos visibles

El Lucidchart SHALL tener demarcación visual de qué clases pertenecen al backend, al microservicio, y qué es interfaz compartida.

#### Scenario: Esterotipos aplicados
- **WHEN** se inspecciona cada clase
- **THEN** las clases del backend SHALL tener "<<backend>>" en su título
- **THEN** las clases del microservicio SHALL tener "<<microservice>>" en su título
- **THEN** Workflow SHALL tener "<<interface>>" en su título

