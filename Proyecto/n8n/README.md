# n8n — Motor de Orquestación de Flujos de Trabajo

## Responsabilidad Arquitectónica

Motor de automatización y orquestación de flujos de trabajo que evalúa reglas de negocio, coordina la secuencia de evaluación clínica y actúa como sistema disparador de notificaciones basado en los eventos y alertas generadas por el ecosistema.

## Alcance Funcional

- Orquestación de flujos de evaluación de triaje desde la captura de datos hasta la generación de alertas.
- Evaluación de reglas de negocio clínicas para determinar prioridades y rutas de atención.
- Disparo de notificaciones al personal médico basado en umbrales de riesgo y eventos del sistema.
- Integración y coordinación entre los distintos módulos del ecosistema (backend, IA, telemetría).
- Automatización de procesos administrativos y clínicos recurrentes.
- Monitoreo y trazabilidad de la ejecución de flujos de trabajo.

## Límites del Módulo

- No ejecuta modelos predictivos ni algoritmos de inteligencia artificial.
- No almacena datos clínicos de forma persistente; delega en la capa de API central.
- No implementa la interfaz de usuario final ni dashboards médicos.
