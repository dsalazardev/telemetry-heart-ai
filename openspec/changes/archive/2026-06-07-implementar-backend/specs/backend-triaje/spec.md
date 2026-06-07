## ADDED Requirements

### Requirement: Crear triaje
El sistema SHALL permitir crear un triaje asociado a un paciente y opcionalmente a un médico. El triaje SHALL incluir probabilidadRiesgo, nivelUrgencia, factoresCriticos, explicacionClinica y diagnosticoConfirmado (nullable).

#### Scenario: Crear triaje para paciente
- **WHEN** se envía `POST /triajes` con paciente_id, probabilidadRiesgo y nivelUrgencia
- **THEN** el triaje se almacena en `triajes` con fechaEmision automática

### Requirement: Listar triajes pendientes
El sistema SHALL permitir listar triajes donde `atendida = false`.

#### Scenario: Listar triajes pendientes
- **WHEN** se envía `GET /triajes/pendientes`
- **THEN** la respuesta contiene solo triajes no atendidos ordenados por fechaEmision

### Requirement: Atender triaje
El sistema SHALL permitir marcar un triaje como atendido, registrando fechaAtencion y el médico que atiende.

#### Scenario: Atender triaje
- **WHEN** se envía `PUT /triajes/{id}/atender` con medico_id
- **THEN** el triaje queda con `atendida = true`, `fechaAtencion` actual y `medico_id` asignado

### Requirement: Notificar vía Telegram
El sistema SHALL enviar notificación Telegram cuando se crea un triaje de alta urgencia. El método `notificarTelegram()` SHALL usar el `telegramChatId` del médico asignado.

#### Scenario: Notificar triaje de alta urgencia
- **WHEN** se crea un triaje con `nivelUrgencia = "alto"` y médico asignado
- **THEN** se envía mensaje al chat de Telegram del médico y `telegramEnviado = true`

### Requirement: Escalar urgencia
El sistema SHALL permitir actualizar el nivelUrgencia de un triaje existente.

#### Scenario: Escalar de medio a alto
- **WHEN** se ejecuta `escalarUrgencia()` cambiando nivel a "alto"
- **THEN** el triaje se actualiza y se dispara notificación si aplica

### Requirement: Consultar logs de triaje
El sistema SHALL permitir consultar los logs asociados a un triaje.

#### Scenario: Ver logs de triaje
- **WHEN** se envía `GET /triajes/{id}/logs`
- **THEN** la respuesta contiene todos los logs ordenados por timestamp descendente
