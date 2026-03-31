from datetime import date
from typing import Optional

from pydantic import BaseModel


class UsageRecord(BaseModel):
    date: date
    model: str = "unknown"
    provider: str = "unknown"
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    requests_count: int = 1
    tag: Optional[str] = None


class ForecastResult(BaseModel):
    date: date
    predicted_cost: float
    lower_bound: float
    upper_bound: float


class BudgetAlert(BaseModel):
    status: str  # on_track, warning, critical
    message: str
    days_until_exceeded: Optional[int] = None
    projected_monthly_cost: float
    budget: float


class UploadSummary(BaseModel):
    records_imported: int
    date_range_start: date
    date_range_end: date
    total_cost: float
    models_found: list[str]
