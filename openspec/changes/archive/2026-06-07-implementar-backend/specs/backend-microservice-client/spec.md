## ADDED Requirements

### Requirement: Cliente HTTP async para microservicio
El sistema SHALL implementar un cliente HTTP async con `httpx.AsyncClient` para comunicarse con el microservicio de predicción.

#### Scenario: Inicializar cliente
- **WHEN** se importa `microservice_client`
- **THEN** el cliente está configurado con base_url desde `Settings.MICROSERVICE_URL`

### Requirement: Solicitar predicción al microservicio
El sistema SHALL enviar una petición POST al microservicio con los datos de una lectura (age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal) y SHALL recibir la predicción.

#### Scenario: Solicitar predicción exitosa
- **WHEN** `evento_service` solicita predicción con datos válidos de lectura
- **THEN** el microservicio responde con JSON que incluye `probabilidad`, `clasificacion` y `tiempoMs`

#### Scenario: Manejar timeout del microservicio
- **WHEN** el microservicio no responde en 10 segundos
- **THEN** el cliente lanza excepción y el evento queda con `estadoProcesamiento = "timeout_microservicio"`

### Requirement: Integrar predicción en flujo de eventos
El sistema SHALL integrar el llamado al microservicio dentro del flujo de evaluación de umbrales del `evento_service`.

#### Scenario: Flujo completo de evaluación
- **WHEN** un evento alcanza el umbral configurado
- **THEN** el `evento_service` solicita predicción al microservicio, recibe resultado, crea triaje y alerta si aplica

### Requirement: Configuración de URL del microservicio
El sistema SHALL leer la URL del microservicio desde `MICROSERVICE_URL` en `Settings`.

#### Scenario: URL configurada
- **WHEN** `Settings` se inicializa con `MICROSERVICE_URL=http://localhost:8001`
- **THEN** el microservice_client apunta a esa URL
