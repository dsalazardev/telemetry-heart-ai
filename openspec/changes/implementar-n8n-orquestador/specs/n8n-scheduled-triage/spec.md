## ADDED Requirements

### Requirement: Revisión periódica de triajes sin atender
El sistema SHALL ejecutar un workflow cada 5 minutos (cron `*/5 * * * *`) que consulte la tabla `triajes` filtrando `atendida = false AND telegramEnviado = false`, notifique al médico por Telegram con detalles del triaje, y actualice `telegramEnviado = true`.

#### Scenario: Hay triajes pendientes
- **WHEN** el Schedule Trigger se activa cada 5 minutos
- **THEN** el nodo PostgreSQL "Triajes Pendientes" ejecuta `SELECT t.id, t.nivelUrgencia, t.probabilidadRiesgo, t.paciente_id, u.nombres, u.apellidos, m.telegramChatId FROM triajes t JOIN pacientes p ON t.paciente_id = p.id JOIN usuarios u ON p.id = u.id JOIN medicos m ON t.medico_id = m.id WHERE t.atendida = false AND t.telegramEnviado = false`
- **AND** si `rowCount > 0`, el flujo envía notificación Telegram a cada `medico.telegramChatId`
- **AND** cada notificación incluye: nombre del paciente, nivel de urgencia, probabilidad de riesgo, y Triaje ID

#### Scenario: No hay triajes pendientes
- **WHEN** el Schedule Trigger se activa y `rowCount == 0`
- **THEN** el flujo genera log `n8n_schedule_empty` con detalle "Revisión periódica: 0 triajes pendientes"
- **AND** no se envía mensaje Telegram a ningún médico
- **AND** no se intenta ejecutar nodos posteriores del flujo (rama IF vacía)

### Requirement: Notificación con formato de alerta médica
El sistema SHALL formatear la notificación como mensaje de alerta cardiovascular usando markdown con emojis, incluyendo nombre del paciente, nivel de urgencia, probabilidad de riesgo, y Triaje ID.

#### Scenario: Formato de alerta para Telegram
- **WHEN** se construye el mensaje de notificación
- **THEN** el texto incluye: `🚨 ALERTA CARDIOVASCULAR`, `Paciente: {nombre} {apellidos}`, `Nivel: {nivelUrgencia} ({probabilidadRiesgo}%)`, `Triaje ID: {id}`, `Fecha: {fechaEmision}`
- **AND** el mensaje está en español y es legible en dispositivos móviles

### Requirement: Actualización de flag telegramEnviado
El sistema SHALL actualizar `triajes.telegramEnviado = true` inmediatamente después de enviar la notificación, para evitar notificaciones duplicadas en la siguiente ejecución del schedule.

#### Scenario: Flag actualizado tras notificación
- **WHEN** se envía notificación Telegram de un triaje pendiente
- **THEN** el nodo PostgreSQL "UPDATE telegramEnviado" ejecuta `UPDATE triajes SET telegramEnviado = true WHERE id = $1`
- **AND** en la siguiente ejecución del schedule (5 min después), ese triaje ya no aparece en el SELECT

#### Scenario: Log de éxito del schedule
- **WHEN** se completan las notificaciones de triajes pendientes
- **THEN** se genera log `n8n_schedule_ok` con detalle incluyendo el número de triajes notificados
- **AND** `exitoso = true`
- **AND** `timestamp = NOW()`
