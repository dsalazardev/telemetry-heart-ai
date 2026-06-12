from typing import Type

from app.services.optimizers.base import BaseOptimizer


class OptimizerRegistry:
    """Registro de metaheurísticas disponibles.
    Ejemplo:
        from app.services.optimizers.registry import optimizer_registry
        from app.services.optimizers.pso import PSOOptimizer
        optimizer_registry.register("pso", PSOOptimizer)
        opt = optimizer_registry.create("pso", n_particles=30, max_iter=100)
    """

    def __init__(self):
        self._optimizers: dict[str, Type[BaseOptimizer]] = {}

    def register(self, name: str, optimizer_cls: Type[BaseOptimizer]) -> None:
        self._optimizers[name] = optimizer_cls

    def create(self, name: str, **kwargs) -> BaseOptimizer:
        if name not in self._optimizers:
            raise ValueError(f"Optimizer no registrado: {name}. Disponibles: {list(self._optimizers.keys())}")
        return self._optimizers[name](**kwargs)

    def available(self) -> list[str]:
        return list(self._optimizers.keys())


optimizer_registry = OptimizerRegistry()
