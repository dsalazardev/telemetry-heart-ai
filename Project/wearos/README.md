# Wear OS — Capa de Adquisición de Telemetría IoT

## Responsabilidad Arquitectónica

Capa de adquisición de telemetría mediante dispositivos vestibles que captura, procesa y transmite de forma continua datos biométricos del paciente hacia el ecosistema central, eliminando la dependencia de captura manual de signos vitales.

## Alcance Funcional

- Captura continua de datos biométricos (frecuencia cardíaca, presión arterial, niveles de oxígeno, entre otros).
- Transmisión en tiempo real de los datos capturados hacia el backend central del ecosistema.
- Procesamiento local básico para detección de anomalías inmediatas en los signos vitales.
- Gestión de la comunicación segura con el servidor central.
- Configuración remota de parámetros de captura y frecuencias de muestreo.
- Indicadores de estado de conectividad y salud del dispositivo.

## Límites del Módulo

- No realiza diagnóstico ni predicción de riesgo cardiovascular; delega esa responsabilidad en la capa de IA.
- No almacena historiales clínicos extensos; transmite los datos al backend para persistencia centralizada.
- No implementa la interfaz de dashboard médico ni la gestión de pacientes.
