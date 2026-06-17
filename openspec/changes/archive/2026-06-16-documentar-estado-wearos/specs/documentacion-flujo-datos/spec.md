## ADDED Requirements

### Requirement: Documentar flujo de datos completo del sistema
El AGENTS.md SHALL documentar el flujo de datos completo desde la captura en WearOS hasta las notificaciones, incluyendo todos los módulos involucrados: WearOS, backend, n8n, microservice, Telegram.

#### Scenario: Flujo principal telemetría
- **WHEN** un agente consulta el flujo de datos
- **THEN** encuentra que WearOS envía POST /telemetria → backend valida y almacena → WebSocket broadcast al dashboard → n8n recibe webhook → llama POST /evaluar en microservice → microservice ejecuta RiskEngine → si threshold superado → alerta → Telegram al médico

### Requirement: Documentar rol de n8n en el flujo
El AGENTS.md SHALL documentar que n8n tiene un workflow (THA-Webhook-Telemetria) que recibe telemetría vía webhook y la reenvía al microservice para evaluación de riesgo. NO es un paso intermedio obligatorio entre WearOS y backend — son rutas paralelas que comparten la misma tabla telemetrias.

#### Scenario: Rutas paralelas
- **WHEN** un agente consulta la relación entre WearOS y n8n
- **THEN** encuentra que WearOS escribe directamente al backend (POST /telemetria), mientras n8n recibe webhooks IoT simulados y también escribe a la misma tabla — son rutas independientes

### Requirement: Documentar detección de anomalías
El AGENTS.md SHALL documentar que el backend detecta anomalías (HR fuera de umbral, SPO2 bajo) y que el microservice puede generar alertas y notificaciones Telegram.

#### Scenario: Umbrales de alerta
- **WHEN** un agente consulta cómo se generan alertas
- **THEN** encuentra que backend valida contra umbrales.json (fc_max=120, fc_min=40, spo2_min=90) y que microservice ejecuta clasificador RandomForest para riesgo cardiovascular

### Requirement: Documentar flujo offline
El AGENTS.md SHALL documentar que actualmente NO hay manejo de conectividad perdida en WearOS — no hay cola offline, no hay almacenamiento local, no hay retry lógica.

#### Scenario: Sin offline
- **WHEN** un agente consulta el estado offline
- **THEN** encuentra que si WearOS pierde conectividad, los datos se pierden — no hay buffer local ni retry
