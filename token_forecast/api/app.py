import logging
from datetime import date
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from token_forecast.api import storage
from token_forecast.config import settings
from token_forecast.forecast.engine import check_budget, forecast_cost
from token_forecast.models import UploadSummary
from token_forecast.parsers.csv_parser import parse_csv

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Token Forecast",
    description="Predict when your LLM spending will exceed budget",
    version="0.1.0",
)

DASHBOARD_PATH = Path(__file__).parent.parent / "dashboard" / "index.html"


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/", include_in_schema=False)
async def root():
    return HTMLResponse(
        '<html><head><meta http-equiv="refresh" content="0;url=/dashboard"></head></html>'
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    if DASHBOARD_PATH.exists():
        return HTMLResponse(DASHBOARD_PATH.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Dashboard not found</h1>", status_code=404)


@app.post("/api/upload", response_model=UploadSummary)
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    content = await file.read()
    try:
        records = parse_csv(content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await storage.store_records(records)

    dates = [r.date for r in records]
    models = list({r.model for r in records})
    return UploadSummary(
        records_imported=len(records),
        date_range_start=min(dates),
        date_range_end=max(dates),
        total_cost=round(sum(r.cost for r in records), 2),
        models_found=sorted(models),
    )


@app.get("/api/forecast")
async def get_forecast():
    records = await storage.get_records()
    if not records:
        raise HTTPException(status_code=404, detail="No usage data. Upload a CSV first.")

    try:
        forecast = forecast_cost(records, days=settings.forecast_days)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    budget_str = await storage.get_setting("budget_monthly", str(settings.budget_monthly))
    budget = float(budget_str)
    alert = check_budget(records, forecast, budget)

    # Historical daily costs for chart
    daily: dict[str, float] = {}
    for r in records:
        key = r.date.isoformat()
        daily[key] = daily.get(key, 0) + r.cost

    historical = [{"date": k, "cost": round(v, 2)} for k, v in sorted(daily.items())]

    return {
        "historical": historical,
        "forecast": [f.model_dump() for f in forecast],
        "alert": alert.model_dump(),
    }


@app.get("/api/usage")
async def get_usage(
    start: date | None = Query(None),
    end: date | None = Query(None),
    limit: int = Query(500, le=5000),
):
    records = await storage.get_records(start_date=start, end_date=end)
    return [r.model_dump() for r in records[:limit]]


@app.get("/api/summary")
async def get_summary():
    records = await storage.get_records()
    if not records:
        return {
            "total_cost": 0,
            "total_records": 0,
            "avg_daily_cost": 0,
            "total_tokens": 0,
            "top_models": [],
            "date_range": None,
        }

    total_cost = sum(r.cost for r in records)
    dates = {r.date for r in records}
    num_days = max(1, len(dates))

    model_costs: dict[str, float] = {}
    for r in records:
        model_costs[r.model] = model_costs.get(r.model, 0) + r.cost

    top_models = sorted(model_costs.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "total_cost": round(total_cost, 2),
        "total_records": len(records),
        "avg_daily_cost": round(total_cost / num_days, 2),
        "total_tokens": sum(r.input_tokens + r.output_tokens for r in records),
        "top_models": [{"model": m, "cost": round(c, 2)} for m, c in top_models],
        "date_range": {
            "start": min(dates).isoformat(),
            "end": max(dates).isoformat(),
        },
    }


class BudgetRequest(BaseModel):
    amount: float


@app.post("/api/budget")
async def set_budget(req: BudgetRequest):
    if req.amount < 0:
        raise HTTPException(status_code=400, detail="Budget must be non-negative")
    await storage.set_setting("budget_monthly", str(req.amount))
    return {"budget_monthly": req.amount}
