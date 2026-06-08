from abc import ABC, abstractmethod

import numpy as np
from pydantic import BaseModel


class OptimizerResult(BaseModel):
    weights: list[float]
    thresholds: list[float]
    bias: float = 0.0
    fitness_history: list[float]
    metrics: dict
    n_generations: int
    computation_time: float
    algorithm: str
    version: str


class BaseOptimizer(ABC):
    @abstractmethod
    def optimize(self, X: np.ndarray, y: np.ndarray) -> OptimizerResult:
        ...
