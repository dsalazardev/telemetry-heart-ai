from pydantic import BaseModel


class MetricsRow(BaseModel):
    accuracy: float = 0.0
    recall_high_risk: float = 0.0
    false_negative_rate: float = 0.0
    f1_score: float = 0.0
    critical_recall: float = 0.0
    overtriage_rate: float = 0.0
    ordinal_error: float = 0.0
    fitness: float = 0.0


class MetricsComparison(BaseModel):
    baseline: MetricsRow
    optimized: MetricsRow
    improvement: MetricsRow
    delta: dict = {}
