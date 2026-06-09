## ADDED Requirements

### Requirement: LLM genera SQL dinámico con filtro medico_id obligatorio
El sistema SHALL enviar un prompt al LLM (OpenAI/Claude) que incluya el esquema completo de la BD, el `medico_id` del médico identificado, y la REGLA ABSOLUTA de filtrar por `medico_id`. El LLM SHALL devolver únicamente la consulta SQL, sin explicaciones.

#### Scenario: Generación de SQL válido con filtro medico_id
- **WHEN** el médico pregunta "Status del paciente 1"
- **THEN** el LLM genera SQL que incluye `WHERE t.medico_id = {medico_id}`
- **AND** el SQL ejecuta correctamente en PostgreSQL
- **AND** retorna datos del paciente 1 solo si pertenece a triajes del médico

#### Scenario: Bloqueo de acceso a datos de otro médico
- **WHEN** el médico pregunta "¿Cuántos pacientes tiene el doctor 3?"
- **THEN** el LLM responde `ERROR_ACCESO: No tienes permiso para ver datos de otro médico`
- **AND** no se ejecuta ninguna consulta SQL
- **AND** se genera log `n8n_llm_query` con detalle de la pregunta y respuesta de bloqueo

#### Scenario: Formato de respuesta del LLM
- **WHEN** el nodo HTTP Request "LLM → Generar SQL" recibe respuesta de OpenAI
- **THEN** el SQL está en `choices[0].message.content`
- **AND** el contenido es únicamente el SQL (o `ERROR_ACCESO`), sin markdown ni explicaciones adicionales

### Requirement: Pipeline de dos llamadas al LLM
El sistema SHALL realizar DOS llamadas independientes al LLM: (1) generar SQL a partir de la pregunta del médico, (2) formatear los resultados de la consulta en texto legible para Telegram.

#### Scenario: Primera llamada genera SQL
- **WHEN** el médico hace una pregunta
- **THEN** la primera llamada al LLM recibe prompt con esquema BD + reglas + medico_id
- **AND** retorna SQL válido (o error de acceso)
- **AND** se genera log `n8n_llm_query` con la pregunta original

#### Scenario: Segunda llamada formatea resultados
- **WHEN** el SQL se ejecuta exitosamente y retorna filas de datos
- **THEN** la segunda llamada al LLM recibe los datos JSON y un prompt para formatearlos
- **AND** retorna texto amigable en español adecuado para Telegram
- **AND** se genera log `n8n_sql_ok` con el SQL ejecutado

### Requirement: Manejo de errores SQL con reintento automático
El sistema SHALL detectar errores en la ejecución del SQL generado por el LLM, capturar el mensaje de error, enviarlo al LLM para regenerar el SQL corregido, reintentar una vez, y si falla nuevamente enviar una disculpa al médico.

#### Scenario: Error SQL en primer intento, éxito en reintento
- **WHEN** el SQL generado por el LLM falla (ej: columna inexistente)
- **THEN** el nodo "Capturar Error SQL" extrae el mensaje de error
- **AND** el nodo "LLM → Regenerar SQL" envía error + pregunta original + reglas al LLM
- **AND** el SQL corregido se ejecuta exitosamente
- **AND** se genera log `n8n_sql_error` para el primer intento y `n8n_sql_reintento` para el éxito

#### Scenario: Error SQL en ambos intentos
- **WHEN** el SQL corregido también falla (segundo intento)
- **THEN** el flujo envía mensaje de disculpa al médico por Telegram: "Lo siento, no pude procesar tu consulta. Por favor intenta de otra forma."
- **AND** se genera log `n8n_sql_fatal` con ambos errores (`errorMsg` concatenado)
- **AND** el flujo termina sin crash ni bucle infinito

### Requirement: Prompt incluye esquema completo y reglas de acceso
El system prompt enviado al LLM SHALL incluir: definición de rol (asistente SQL cardiovascular), `medico_id` del médico actual, REGLA ABSOLUTA de filtrar por `medico_id`, esquema completo de las 12 tablas con restricciones de acceso por relaciones UML, e instrucción de devolver solo SQL.

#### Scenario: Prompt contiene esquema de 12 tablas
- **WHEN** el nodo "Armar Prompt SQL" construye el prompt
- **THEN** incluye las 12 tablas: `usuarios`, `pacientes`, `medicos`, `triajes`, `alertas`, `logs`, `telemetrias`, `eventos`, `perfiles`, `patologias`, `historiales`, `dispositivos`
- **AND** cada tabla tiene indicada su restricción de acceso (ej: "→ SIEMPRE filtrar por medico_id")

#### Scenario: Prompt incluye REGLA ABSOLUTA
- **WHEN** se inspecciona el prompt enviado al LLM
- **THEN** contiene la frase exacta: "REGLA ABSOLUTA: TODAS las consultas SQL deben incluir WHERE medico_id = {medico_id} o el filtro equivalente"
- **AND** contiene la instrucción: "Si la pregunta intenta acceder a datos de otro médico, responde: ERROR_ACCESO..."
