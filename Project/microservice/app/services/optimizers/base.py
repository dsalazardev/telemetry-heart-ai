from abc import ABC, abstractmethod

import numpy as np
from pydantic import BaseModel


class OptimizerResult(BaseModel):
    """Resultado de ejecutar una metaheurística (PSO).

    Campos canónicos para PSO de prioridad clínica:
      - weights               : 7 pesos clínicos (list[float])
      - thresholds            : 3 umbrales (t_medium, t_high, t_critical)
      - priority_thresholds   : alias explícito de `thresholds` para consumidores
      - feature_weights_dict  : {feature_name: weight} para el priority service
      - convergence_curve     : fitness por iteración
      - best_fitness          : fitness final
      - metrics               : dict con accuracy, f1, critical_recall, etc.
      - critical_recall, overtriage_rate, ordinal_error : réplicas para consumers
    """

    weights: list[float]
    thresholds: list[float]
    bias: float = 0.0
    fitness_history: list[float] = []
    convergence_curve: list[float] = []
    best_fitness: float = 0.0
    runtime_ms: int = 0
    metrics: dict
    n_generations: int
    computation_time: float
    algorithm: str
    version: str

    priority_thresholds: list[float] = []
    feature_weights_dict: dict[str, float] = {}
    critical_recall: float | None = None
    overtriage_rate: float | None = None
    ordinal_error: float | None = None


class BaseOptimizer(ABC):
    @abstractmethod
    def optimize(self, X: np.ndarray, y: np.ndarray) -> OptimizerResult:
        ...
