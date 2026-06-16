## ADDED Requirements

### Requirement: Documentar endpoint POST /dispositivos
El AGENTS.md SHALL documentar el endpoint de registro de dispositivos incluyendo método, ruta, body de request, schema de response y mecanismo de autenticación.

#### Scenario: Contrato de registro completo
- **WHEN** un agente consulta cómo registrar un dispositivo WearOS
- **THEN** encuentra que POST /dispositivos espera `{"tipo": "WearOS", "modelo": "...", "sistemaOperativo": "...", "paciente_id": int}` y retorna `{"id": int, "tokenAutenticacion": "JWT..."}`

### Requirement: Documentar endpoint POST /telemetria
El AGENTS.md SHALL documentar el endpoint de envío de telemetría incluyendo método, ruta, headers de autenticación, body de request, schema de response, códigos de estado HTTP y rangos de validación.

#### Scenario: Contrato de telemetría completo
- **WHEN** un agente consulta cómo enviar datos biométricos
- **THEN** encuentra que POST /telemetria requiere header `Authorization: Bearer <token>`, body con `frecuenciaCardiaca`, `spo2`, `timestamp`, `dispositivo_id`, y retorna 201 con estadoProcesamiento

#### Scenario: Validaciones del backend
- **WHEN** un agente consulta rangos válidos
- **THEN** encuentra que frecuenciaCardiaca debe estar entre 30 y 220, spo2 entre 0 y 100, y que umbrales.json define fc_max=120, fc_min=40, spo2_min=90

### Requirement: Documentar autenticación JWT
El AGENTS.md SHALL documentar el mecanismo de autenticación: cómo se genera el token en create_device_token(), algoritmo (HS256), claims (sub, type, exp), y tiempo de expiración (30 días).

#### Scenario: Token device
- **WHEN** un agente consulta cómo funciona la autenticación
- **THEN** encuentra que el token se genera con create_device_token(id) en el backend, usa HS256, expira en 30 días, y se envía como Bearer en cada POST /telemetria

### Requirement: Documentar WebSocket /ws/telemetria/{id}
El AGENTS.md SHALL documentar el endpoint WebSocket para broadcast en tiempo real, incluyendo ruta, query parameter de token, y formato del mensaje broadcast.

#### Scenario: WebSocket broadcast
- **WHEN** un agente consulta el WebSocket
- **THEN** encuentra que ws://host/ws/telemetria/{paciente_id}?token=JWT emite mensajes con `{"tipo": "telemetria", "fc": float, "spo2": float, "timestamp": "ISO8601"}`
