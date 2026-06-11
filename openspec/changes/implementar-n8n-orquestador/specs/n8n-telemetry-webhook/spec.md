## ADDED Requirements

### Requirement: Webhook recibe telemetría de WearOS
El sistema SHALL exponer un endpoint webhook POST en `/webhook/telemetria` que reciba datos de telemetría (`paciente_id`, `frecuenciaCardiaca`, `spo2`, `anomaliaEcg`), los persista en la tabla `telemetrias` de PostgreSQL, y responda HTTP 200 al emisor.

#### Scenario: Telemetría recibida y almacenada
- **WHEN** un dispositivo WearOS (o simulación curl) envía POST a `/webhook/telemetria` con body `{ paciente_id: 1, frecuenciaCardiaca: 120, spo2: 88, anomaliaEcg: "ST-elevation" }`
- **THEN** n8n recibe el webhook y responde HTTP 200
- **AND** el nodo PostgreSQL "INSERT Telemetría" ejecuta INSERT INTO telemetrias con los datos recibidos y `dispositivo_id` obtenido de `SELECT id FROM dispositivos WHERE paciente_id = $paciente_id AND activo = true LIMIT 1`
- **AND** el campo `estadoProcesamiento` es `'recibida'`

#### Scenario: Telemetría sin dispositivo activo
- **WHEN** el webhook recibe telemetría para un `paciente_id` sin dispositivos activos
- **THEN** el SELECT de `dispositivos` retorna NULL
- **AND** el INSERT en `telemetrias` usa `dispositivo_id = NULL`
- **AND** se genera log `n8n_webhook_ok` con detalle indicando dispositivo no encontrado

### Requirement: Notificación al microservicio de evaluación
El sistema SHALL enviar los datos de telemetría recibidos al microservicio vía HTTP POST a `{{$env.MICROSERVICE_URL}}/evaluar` con timeout de 10 segundos, y registrar el resultado.

#### Scenario: Microservicio responde exitosamente
- **WHEN** el nodo "Notificar Microservicio" envía POST a `MICROSERVICE_URL/evaluar` con el payload de telemetría
- **THEN** el microservicio responde HTTP 200 en menos de 10 segundos
- **AND** se genera log `n8n_micro_ok` con detalle incluyendo `paciente_id`
- **AND** el flujo continúa normalmente

#### Scenario: Microservicio no responde o devuelve error
- **WHEN** el microservicio no responde (timeout 10s) o responde HTTP 4xx/5xx
- **THEN** el nodo HTTP Request captura el error
- **AND** se genera log `n8n_micro_error` con `errorMsg` incluyendo el error HTTP o "timeout"
- **AND** el flujo continúa sin interrumpir el almacenamiento de telemetría
- **AND** la telemetría ya está persistida en BD — no se pierde

### Requirement: Log de recepción de telemetría
El sistema SHALL generar un log `n8n_webhook_ok` inmediatamente después de almacenar la telemetría, con detalle incluyendo `paciente_id`, `frecuenciaCardiaca`, y `spo2`.

#### Scenario: Log detallado de telemetría
- **WHEN** se completa el INSERT de telemetría en PostgreSQL
- **THEN** se genera log con `tipoEvento = 'n8n_webhook_ok'`
- **AND** `detalle` incluye: "Telemetría paciente {paciente_id}: FC={frecuenciaCardiaca}, SpO2={spo2}"
- **AND** `exitoso = true`
- **AND** `timestamp = NOW()`
- **AND** `triaje_id = NULL` (la telemetría no está asociada a un triaje específico aún)

### Requirement: Webhook responde al emisor
El sistema SHALL responder HTTP 200 al dispositivo WearOS (o simulador) inmediatamente después de recibir la telemetría, antes de procesar el microservicio.

#### Scenario: Respuesta inmediata al emisor
- **WHEN** llega POST a `/webhook/telemetria`
- **THEN** el nodo Webhook responde HTTP 200 con body "Telemetría recibida"
- **AND** la respuesta se envía ANTES de ejecutar los nodos PostgreSQL INSERT y HTTP Request al microservicio
- **AND** el emisor no espera a que termine el procesamiento completo
