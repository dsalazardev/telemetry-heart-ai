## ADDED Requirements

### Requirement: Recibir telemetría desde WearOS
El sistema SHALL recibir telemetría vía `POST /telemetria` con token Bearer del dispositivo. Los datos SHALL incluir frecuenciaCardiaca, anomaliaEcg, spo2 y timestamp.

#### Scenario: Enviar telemetría válida
- **WHEN** un dispositivo envía `POST /telemetria` con JWT válido y datos completos
- **THEN** la telemetría se almacena en `telemetrias` con `estadoProcesamiento = "recibida"`

#### Scenario: Rechazar telemetría sin token
- **WHEN** se envía `POST /telemetria` sin header Authorization
- **THEN** la respuesta es HTTP 401

### Requirement: Validar telemetría
El sistema SHALL validar rangos de telemetría (ej: fc entre 30 y 220, spo2 entre 0 y 100). Datos inválidos SHALL ser rechazados.

#### Scenario: Rechazar frecuencia cardíaca inválida
- **WHEN** se envía telemetría con `frecuenciaCardiaca = 300`
- **THEN** la respuesta es HTTP 422 con detalle del campo inválido

### Requirement: Asignar telemetría a evento
El sistema SHALL agregar telemetrías a un evento activo (dentro de la ventana de tiempo). Si no hay evento activo, SHALL crear uno nuevo.

#### Scenario: Agregar a evento existente
- **WHEN** llega telemetría dentro de la ventana de 5 min de un evento activo
- **THEN** la telemetría se vincula al evento existente y `lecturas` incrementa

#### Scenario: Crear nuevo evento
- **WHEN** llega telemetría y no hay evento activo
- **THEN** se crea un nuevo `Evento` con `ventanaInicio = now` y `ventanaFin = now + 5 min`

### Requirement: Enriquecer telemetría con laboratorio
El sistema SHALL permitir enriquecer una telemetría con datos de laboratorio posteriormente.

#### Scenario: Enriquecer telemetría
- **WHEN** se ejecuta `enriquecerConLab()` con datos adicionales
- **THEN** la telemetría se actualiza y `estadoProcesamiento = "enriquecida"`
