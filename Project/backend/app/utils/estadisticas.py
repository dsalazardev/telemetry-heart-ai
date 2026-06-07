import random
from datetime import datetime

import simpy
import numpy as np


def simular_triaje(env, paciente_id, tiempo_llegada, tiempo_atencion, resultados):
    """Proceso de SimPy que simula la llegada de un paciente, su triaje y alerta."""
    yield env.timeout(tiempo_llegada)
    llegada = env.now
    resultados.append({"evento": "llegada", "paciente_id": paciente_id, "tiempo": llegada})

    yield env.timeout(tiempo_atencion)
    atencion = env.now
    resultados.append({"evento": "atencion", "paciente_id": paciente_id, "tiempo": atencion})

    # Simular probabilidad de riesgo
    probabilidad = random.uniform(0.0, 1.0)
    nivel = "bajo" if probabilidad < 0.3 else "medio" if probabilidad < 0.7 else "alto"
    resultados.append({
        "evento": "triaje",
        "paciente_id": paciente_id,
        "probabilidad": round(probabilidad, 2),
        "nivel": nivel,
        "tiempo": atencion,
    })

    if nivel == "alto":
        resultados.append({"evento": "alerta", "paciente_id": paciente_id, "tiempo": atencion})


def run_simulation(n_pacientes: int = 30, tasa_llegada: float = 2.0, t_media_atencion: float = 5.0):
    """
    Ejecuta una simulación de triaje con SimPy.
    n_pacientes: número de pacientes a simular
    tasa_llegada: tiempo promedio entre llegadas (min)
    t_media_atencion: tiempo promedio de atención (min)
    """
    env = simpy.Environment()
    resultados = []

    for i in range(n_pacientes):
        tiempo_llegada = np.random.exponential(tasa_llegada)
        tiempo_atencion = np.random.exponential(t_media_atencion)
        env.process(simular_triaje(env, i + 1, tiempo_llegada, tiempo_atencion, resultados))

    env.run()
    return resultados


def generar_resumen(resultados):
    """Genera un resumen estadístico de la simulación."""
    triajes = [r for r in resultados if r["evento"] == "triaje"]
    alertas = [r for r in resultados if r["evento"] == "alerta"]

    if not triajes:
        return {}

    probabilidades = [t["probabilidad"] for t in triajes]
    niveles = {"bajo": 0, "medio": 0, "alto": 0}
    for t in triajes:
        niveles[t["nivel"]] += 1

    return {
        "total_pacientes": len(triajes),
        "total_alertas": len(alertas),
        "prob_media": round(np.mean(probabilidades), 2),
        "prob_max": round(np.max(probabilidades), 2),
        "niveles": niveles,
    }
