# Frontend — Interfaz de Usuario y Dashboard Médico

## Responsabilidad Arquitectónica

Capa de presentación del ecosistema. Su función es proporcionar una interfaz visual interactiva para que el personal médico pueda monitorear en tiempo real las alertas generadas por el sistema de triaje, visualizar dashboards con métricas clave de pacientes, y gestionar el flujo de evaluación clínica.

## Alcance Funcional

- Visualización en tiempo real de alertas de riesgo cardiovascular.
- Dashboard interactivo con métricas de triaje, estado de pacientes y tendencias.
- Gestión del flujo de trabajo de evaluación clínica.
- Presentación de resultados del modelo predictivo y explicaciones generadas por el agente conversacional.
- Visualización de datos de telemetría provenientes de dispositivos vestibles.
- Interfaz de administración de pacientes y configuración del sistema.

## Límites del Módulo

- No implementa lógica de negocio ni reglas de predicción clínica.
- No persiste datos directamente; toda la información se obtiene a través de la capa de API.
- No ejecuta procesamiento de señales biomédicas ni algoritmos de inteligencia artificial.
