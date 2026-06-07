## ADDED Requirements

### Requirement: Emitir alerta
El sistema SHALL crear alertas con tipo, mensaje, paciente_id y opcionalmente medico_id. La alerta SHALL nacer con `leida = false` y `atendida = false`.

#### Scenario: Crear alerta para paciente
- **WHEN** el sistema detecta una anomalía y emite alerta
- **THEN** se almacena en `alertas` con `fechaEmision` automática

### Requirement: Marcar alerta como leída
El sistema SHALL permitir marcar una alerta como leída.

#### Scenario: Marcar alerta leída
- **WHEN** se envía `PUT /alertas/{id}/leer`
- **THEN** el campo `leida` pasa a `true`

### Requirement: Asignar médico a alerta
El sistema SHALL permitir asignar un médico a una alerta.

#### Scenario: Asignar médico
- **WHEN** se envía `PUT /alertas/{id}/asignar` con medico_id
- **THEN** el campo `medico_id` se actualiza y la alerta queda asignada

### Requirement: Atender alerta
El sistema SHALL permitir marcar una alerta como atendida, registrando fechaAtencion.

#### Scenario: Atender alerta
- **WHEN** se envía `PUT /alertas/{id}/atender`
- **THEN** `atendida = true` y `fechaAtencion` se establece

### Requirement: Listar alertas
El sistema SHALL listar alertas con filtros opcionales por paciente, médico y estado.

#### Scenario: Listar alertas no atendidas
- **WHEN** se envía `GET /alertas?atendida=false`
- **THEN** la respuesta contiene solo alertas pendientes
