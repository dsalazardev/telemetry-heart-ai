from pydantic import BaseModel


class MetricsRow(BaseModel):
    accuracy: float
    recall_high_risk: float
    false_negative_rate: float
    f1_score: float


class MetricsComparison(BaseModel):
    baseline: MetricsRow
    optimized: MetricsRow
    improvement: MetricsRow
    delta: dict = {}
