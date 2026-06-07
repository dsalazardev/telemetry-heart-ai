# ADR-007: SimPy para Simulación de Procesos en la Demo

**Fecha:** 2026-06-07
**Estado:** Aceptado

## Contexto

El proyecto requiere una demo en vivo de 10 minutos. Con solo 30 pacientes simulados, la demo puede ser estática (datos prefijados) o dinámica (eventos ocurren en tiempo real).

Necesitamos:
- Generar flujo continuo de telemetría durante la demo
- Simular llegada de pacientes a urgencias
- Mostrar cómo se comporta el sistema bajo carga
- Producir métricas de rendimiento (tiempo de espera, pacientes atendidos, etc.)

## Opciones Consideradas

### Opción 1: Datos prefijados (sin simulación)
- Cargar datos del CSV directamente en la BD
- La demo muestra consultas a datos históricos
- Sin eventos en tiempo real, sin dinámica

### Opción 2: SimPy (Simulation Process)
- SimPy genera pacientes, telemetría y eventos en tiempo real
- Los procesos de SimPy alimentan el backend vía API
- La demo muestra el sistema "vivo"
- Se pueden generar métricas de simulación (throughput, tiempos de espera)

### Opción 3: Script manual con time.sleep()
- Un script que cada N segundos hace POST al backend
- Simple pero sin modelo conceptual de simulación
- Difícil de mostrar en la presentación

## Decisión

**SimPy para simulación de procesos + datos prefijados del CSV como baseline**

## Fundamentos

1. **Demo viva**: La audiencia ve pacientes llegando, alertas generándose, médicos atendiendo. Es más impresionante que una tabla estática.
2. **Métricas en vivo**: SimPy permite calcular tiempo promedio de atención, pacientes en cola, tasa de falsos positivos — todo durante la demo.
3. **Los 3 niveles**: La simulación se conecta con n8n (N1) y LangChain (N2), y las métricas alimentan el análisis de metaheurísticas (N3).
4. **Código defendible**: "Usamos SimPy para modelar el proceso de triaje como una simulación de eventos discretos" es exactamente el tipo de respuesta que un docente quiere escuchar en Q&A.

## Consecuencias

- Positivas: Demo dinámica, métricas en vivo, código interesante de mostrar
- Positivas: SimPy es simple de implementar (generators de Python)
- Negativas: Dependencia extra en requirements.txt
- Negativas: La simulación debe sincronizarse con tiempo real (1 segundo de simulación = 1 segundo real, o acelerado)

## Estructura Propuesta

```python
# utils/estadisticas.py

import simpy
import random
from datetime import datetime, timedelta

class SimulacionTriaje:
    """Simula la llegada de pacientes y generación de telemetría."""

    def __init__(self, env: simpy.Environment):
        self.env = env
        self.pacientes_atendidos = 0
        self.tiempos_espera = []

    def llegada_paciente(self):
        """Proceso: un paciente llega cada ~10 minutos."""
        while True:
            yield self.env.timeout(random.expovariate(1/10))
            # Llamar API del backend para crear paciente + telemetría
            self.pacientes_atendidos += 1

    def generar_telemetria(self, paciente_id: str):
        """Proceso: cada paciente genera telemetría cada 5 minutos."""
        while True:
            yield self.env.timeout(5)
            # POST /api/telemetria con datos sintéticos del CSV
```

## Riesgos

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| Simulación muy lenta para la demo | Media | Acelerar tiempo: 1 min simulado = 5 seg reales |
| Datos sintéticos no realistas | Media | Usar distribuciones del CSV original (edad, sexo, etc.) |
| Complejidad extra explicar SimPy en Q&A | Baja | "SimPy modela el proceso de llegada de pacientes como una cadena de Markov. Cada paciente tiene un tiempo entre llegadas exponencial." |

## Referencias

- [SimPy Documentation](https://simpy.readthedocs.io/)
- ctx7: `/websites/simpy_readthedocs_io_en` — SimPy 3/4
- [SimPy: Process-based Discrete-Event Simulation](https://simpy.readthedocs.io/en/latest/topical_guides/introduction.html)
