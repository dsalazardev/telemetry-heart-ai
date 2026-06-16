from typing import Literal

from pydantic import BaseModel, Field, field_validator


class OptimizeUploadRequest(BaseModel):
    """Payload para `/optimize`: resultado de PSO listo para persistir.

    El endpoint NO ejecuta PSO; sólo valida y guarda los pesos en
    `optimized_weights.json` y la curva de convergencia en
    `convergence_curve.json`. La fuente típica es el `@tool`
    `optimize_triage_priority_tool` ejecutado desde LangGraph Studio.
    """

    weights: list[float] = Field(..., min_length=7, max_length=7)
    thresholds: list[float] = Field(..., min_length=2, max_length=2)
    version: str = Field(..., min_length=1, max_length=64)
    algorithm: Literal["PSO"] = "PSO"
    feature_weights_dict: dict[str, float] = Field(default_factory=dict)
    metrics: dict = Field(default_factory=dict)
    convergence_curve: list[float] = Field(default_factory=list)

    @field_validator("thresholds")
    @classmethod
    def _thresholds_ascending(cls, v: list[float]) -> list[float]:
        if not (v[0] < v[1]):
            raise ValueError("thresholds debe estar estrictamente ascendente (t_medium < t_high)")
        if not all(0.0 <= t <= 1.0 for t in v):
            raise ValueError("thresholds fuera de [0, 1]")
        return v

    @field_validator("weights")
    @classmethod
    def _weights_in_unit(cls, v: list[float]) -> list[float]:
        if not all(0.0 <= w <= 1.0 for w in v):
            raise ValueError("weights fuera de [0, 1]")
        return v


class OptimizeUploadResponse(BaseModel):
    status: Literal["persisted"] = "persisted"
    version: str
    weights_path: str
    curve_path: str | None = None
    n_iterations: int
    best_fitness: float
    critical_recall: float | None = None
