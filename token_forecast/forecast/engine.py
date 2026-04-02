import logging
from datetime import date

import pandas as pd

from token_forecast.models import BudgetAlert, ForecastResult, UsageRecord

logger = logging.getLogger(__name__)


def forecast_cost(records: list[UsageRecord], days: int = 30) -> list[ForecastResult]:
    """Generate a cost forecast using Prophet time-series model.

    Aggregates records by day, fits a Prophet model, and returns predicted daily
    costs with upper/lower confidence bounds for the next `days` days.
    """
    if not records:
        raise ValueError("No usage records to forecast from")

    # Aggregate daily costs
    df = pd.DataFrame([{"ds": r.date, "y": r.cost} for r in records])
    df = df.groupby("ds", as_index=False).agg({"y": "sum"})
    df["ds"] = pd.to_datetime(df["ds"])
    df = df.sort_values("ds")

    if len(df) < 3:
        raise ValueError("Need at least 3 days of data for forecasting")

    # Lazy import Prophet (slow to load, only needed when forecasting)
    from prophet import Prophet

    model = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=len(df) >= 14,
        daily_seasonality=False,
        changepoint_prior_scale=0.1,
    )
    model.fit(df)

    future = model.make_future_dataframe(periods=days)
    prediction = model.predict(future)

    # Extract only the forecast period (after the last historical date)
    last_date = df["ds"].max()
    forecast_df = prediction[prediction["ds"] > last_date]

    results = []
    for _, row in forecast_df.iterrows():
        results.append(
            ForecastResult(
                date=row["ds"].date(),
                predicted_cost=max(0, round(row["yhat"], 2)),
                lower_bound=max(0, round(row["yhat_lower"], 2)),
                upper_bound=max(0, round(row["yhat_upper"], 2)),
            )
        )

    return results


def check_budget(
    records: list[UsageRecord],
    forecast: list[ForecastResult],
    monthly_budget: float,
) -> BudgetAlert:
    """Check whether the forecasted spend will exceed the monthly budget.

    Returns an alert with status: on_track (<80%), warning (80-95%), critical (>95%).
    """
    if monthly_budget <= 0:
        return BudgetAlert(
            status="on_track",
            message="No budget set. Configure a monthly budget to enable alerts.",
            projected_monthly_cost=0,
            budget=0,
        )

    # Calculate current month's actual spend
    today = date.today()
    current_month_start = today.replace(day=1)
    actual_spend = sum(r.cost for r in records if r.date >= current_month_start)

    # Project remaining days from forecast
    remaining_forecast = [f for f in forecast if f.date.month == today.month and f.date > today]
    projected_remaining = sum(f.predicted_cost for f in remaining_forecast)
    projected_total = actual_spend + projected_remaining

    # If no forecast data for current month, extrapolate from daily average
    if not remaining_forecast and records:
        days_elapsed = max(1, (today - current_month_start).days)
        daily_avg = actual_spend / days_elapsed
        days_in_month = 30
        projected_total = daily_avg * days_in_month

    ratio = projected_total / monthly_budget

    # Calculate days until budget exceeded
    days_until = None
    if ratio > 1.0:
        cumulative = actual_spend
        for i, f in enumerate(forecast):
            cumulative += f.predicted_cost
            if cumulative >= monthly_budget:
                days_until = i + 1
                break

    proj = f"${projected_total:,.0f}"
    budg = f"${monthly_budget:,.0f}"

    if ratio >= 0.95:
        status = "critical"
        if days_until:
            message = f"Budget will be exceeded in ~{days_until} days. Projected: {proj} / {budg}"
        else:
            message = f"Projected spend {proj} is {ratio:.0%} of {budg} budget"
    elif ratio >= 0.80:
        status = "warning"
        message = f"Trending high. Projected: {proj} / {budg} ({ratio:.0%})"
    else:
        status = "on_track"
        message = f"On track. Projected: {proj} / {budg} ({ratio:.0%})"

    return BudgetAlert(
        status=status,
        message=message,
        days_until_exceeded=days_until,
        projected_monthly_cost=round(projected_total, 2),
        budget=monthly_budget,
    )
