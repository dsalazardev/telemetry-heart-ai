## ADDED Requirements

### Requirement: Bot de Telegram recibe mensajes de médicos registrados
El sistema SHALL recibir mensajes de Telegram a través de un bot configurado con `TELEGRAM_BOT_TOKEN`, identificar al médico por su `telegramChatId`, y procesar solo mensajes de médicos existentes en la tabla `medicos`.

#### Scenario: Mensaje de médico registrado
- **WHEN** un médico con `telegramChatId` válido en tabla `medicos` envía un mensaje al bot
- **THEN** n8n recibe el webhook de Telegram con `chat_id`, `text`, y `message_id`
- **AND** el flujo principal continúa al nodo de identificación de médico

#### Scenario: Mensaje de usuario no registrado
- **WHEN** un usuario sin `telegramChatId` en tabla `medicos` envía mensaje al bot
- **THEN** n8n recibe el mensaje pero no procesa la solicitud (NoOp / ignora)
- **AND** no se genera consulta SQL ni respuesta al usuario
- **AND** se genera log `n8n_telegram_error` con detalle "Chat ID no registrado"

#### Scenario: Identificación de médico por telegramChatId
- **WHEN** el nodo PostgreSQL "Identificar Médico" ejecuta `SELECT id, nombres, apellidos FROM medicos JOIN usuarios WHERE telegramChatId = :chat_id`
- **THEN** retorna exactamente un registro con `id` del médico y datos del usuario
- **AND** si `rowCount == 0`, el flujo termina sin error ni respuesta

### Requirement: Respuesta de Telegram al chat original
El sistema SHALL enviar la respuesta generada por el LLM al mismo `chat_id` desde el cual llegó el mensaje, usando el nodo Telegram Reply.

#### Scenario: Respuesta exitosa al médico
- **WHEN** el flujo principal completa la consulta y formatea la respuesta
- **THEN** el nodo "Responder Médico" envía mensaje de Telegram al `chat_id` original
- **AND** el mensaje contiene texto legible en español con los datos solicitados
- **AND** se genera log `n8n_telegram_ok` con detalle incluyendo el chat_id

#### Scenario: Fallo al enviar mensaje Telegram
- **WHEN** el nodo Telegram Reply falla (bot bloqueado, chat_id inválido, rate limit)
- **THEN** el flujo captura el error y genera log `n8n_telegram_error` con `errorMsg`
- **AND** el flujo continúa sin interrumpir el resto de la ejecución

### Requirement: TELEGRAM_CHAT_ID no está hardcodeado
El sistema SHALL obtener el `chat_id` dinámicamente de cada mensaje entrante y del campo `medicos.telegramChatId`, nunca desde variables de entorno ni código estático.

#### Scenario: Chat ID dinámico por mensaje
- **WHEN** llega un mensaje de Telegram al bot
- **THEN** el `chat_id` se extrae del payload del webhook de Telegram (`message.chat.id`)
- **AND** nunca se lee de `$env.TELEGRAM_CHAT_ID` ni de ninguna variable estática

#### Scenario: Chat ID del médico en consultas programadas
- **WHEN** el flujo "Schedule Pendientes" consulta triajes sin atender
- **THEN** obtiene `telegramChatId` del JOIN con tabla `medicos`
- **AND** envía notificación al chat_id específico de cada médico con triajes pendientes
