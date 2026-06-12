# Protocolo de Triaje para Eventos Cardíacos — Demo

## Evaluación Inicial

Ante un paciente con telemetría anómala:

1. Evaluar signos vitales: frecuencia cardiaca, SpO2, presión arterial
2. Identificar factores de riesgo preexistentes
3. Calcular score de riesgo cardiovascular

## Criterios de Priorización

- **Prioridad CRÍTICA**: Score ≥ 0.70 o presencia de 3+ signos de alarma
  - Acción: Alerta inmediata al médico de turno
  - Notificación: Telegram con detalle de signos críticos

- **Prioridad ALTA**: Score 0.50-0.69 o 1-2 signos de alarma
  - Acción: Programar evaluación médica en < 30 minutos
  - Monitoreo continuo cada 5 minutos

- **Prioridad MEDIA**: Score < 0.50 sin signos de alarma
  - Acción: Monitoreo de rutina
  - Nueva evaluación en 1 hora o ante cambio de signos

## Recomendaciones

- No retrasar atención ante dolor torácico agudo independientemente del score
- La priorización es una herramienta de apoyo, no reemplaza el criterio médico
- Re-evaluar ante cualquier deterioro de signos vitales
