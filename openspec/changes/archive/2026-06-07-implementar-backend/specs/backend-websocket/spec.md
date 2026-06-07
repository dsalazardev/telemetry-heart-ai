## ADDED Requirements

### Requirement: WebSocket para telemetría en vivo
El sistema SHALL exponer `WS /ws/telemetria/{paciente_id}` para que el frontend se suscriba a telemetría en tiempo real. La conexión SHALL requerir JWT válido en query param `?token=...`.

#### Scenario: Conexión WebSocket exitosa
- **WHEN** el frontend abre `ws://host/ws/telemetria/42?token=<jwt_valido>`
- **THEN** la conexión se establece y el backend registra el websocket en un mapa `{paciente_id: [ws]}`

#### Scenario: Rechazar conexión sin token
- **WHEN** el frontend abre `ws://host/ws/telemetria/42` sin token
- **THEN** la conexión se cierra con código 1008 (policy violation)

### Requirement: Broadcast de telemetría a suscriptores
El sistema SHALL reenviar cada telemetría válida recibida por `POST /telemetria` a todos los WebSocket suscritos al paciente del dispositivo.

#### Scenario: Broadcast tras POST /telemetria
- **WHEN** un dispositivo envía telemetría válida para el paciente 42
- **THEN** todos los websockets suscritos al paciente 42 reciben el mensaje JSON con fc, spo2 y timestamp

### Requirement: Formato de mensajes WebSocket
El sistema SHALL enviar mensajes JSON con formato `{ "tipo": "telemetria", "fc": <float>, "spo2": <float>, "timestamp": "<iso>" }`.

#### Scenario: Verificar formato del mensaje
- **WHEN** se recibe un broadcast de telemetría
- **THEN** el mensaje contiene los campos "tipo", "fc", "spo2" y "timestamp"

### Requirement: Manejo de desconexiones
El sistema SHALL eliminar un websocket del mapa de suscriptores cuando se cierra la conexión.

#### Scenario: Desconexión limpia
- **WHEN** el frontend cierra el WebSocket
- **THEN** el websocket se remueve del mapa y ya no recibe broadcasts
