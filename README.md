# Token Forecast

Predict when your LLM spending will exceed budget.

Upload your usage data, get a cost forecast with confidence intervals, and receive alerts before you overshoot.

## The Problem

53% of AI teams exceed their cost forecasts by 40%+. Enterprise LLM spend doubled in 6 months. Most teams discover they're over budget **after the bill arrives**.

Token Forecast gives you the forecast **before** the surprise.

## How It Works

```
1. Export your usage data (CSV from OpenAI, Anthropic, or any provider)
2. Upload it to Token Forecast
3. See a 30-day cost projection with confidence bands
4. Get alerts: on-track, warning, or critical
```

## Quick Start

```bash
# Install
pip install -e .

# Run
token-forecast

# Open http://localhost:8000/dashboard
```

Or with Docker:

```bash
docker-compose up
```

Then upload `sample_data/example_usage.csv` to see it in action.

## Features

- **Cost Forecasting** — Prophet-based 30-day projections with upper/lower bounds
- **Budget Alerts** — On-track / warning / critical status with days-until-exceeded
- **Multi-Provider** — Supports OpenAI, Anthropic, and generic CSV formats
- **Auto-Detect** — Column format detected automatically from headers
- **Token Pricing** — Estimates cost from token counts if cost column is missing
- **Built-in Dashboard** — Dark-themed monitoring UI, no build step required
- **REST API** — Programmatic access to forecasts and usage data
- **SQLite Storage** — Persistent usage history, zero configuration

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service status |
| `/api/upload` | POST | Upload usage CSV |
| `/api/forecast` | GET | Get cost forecast + budget alert |
| `/api/usage` | GET | Query stored usage records |
| `/api/summary` | GET | Aggregate stats (total, avg, top models) |
| `/api/budget` | POST | Set monthly budget threshold |
| `/dashboard` | GET | Web dashboard |

## CSV Format

The minimum required columns are `date` and `cost`. Additional columns improve forecasting:

```csv
date,model,provider,input_tokens,output_tokens,cost,requests
2025-03-01,gpt-4o,openai,125000,45000,1.45,52
2025-03-01,claude-sonnet-4-20250514,anthropic,89000,32000,0.84,38
```

If `cost` is missing but token columns are present, costs are estimated from built-in pricing data.

## Configuration

Set via environment variables or `.env` file:

```
TOKEN_FORECAST_PORT=8000           # Server port
TOKEN_FORECAST_BUDGET_MONTHLY=5000 # Monthly budget in dollars
TOKEN_FORECAST_FORECAST_DAYS=30    # Forecast horizon
```

## Tech Stack

- **Python 3.10+** with **FastAPI** and **uvicorn**
- **Prophet** for time-series forecasting
- **Plotly.js** for interactive charts
- **SQLite** for persistent storage
- **htmx + Tailwind CSS** for the dashboard (no build step)

## Project Structure

```
token_forecast/
  __main__.py          # Entry point
  config.py            # Pydantic settings
  models.py            # Data models
  parsers/
    csv_parser.py      # Multi-format CSV parsing
    pricing.py         # LLM pricing data
  forecast/
    engine.py          # Prophet forecasting + budget alerts
  api/
    app.py             # FastAPI routes
    storage.py         # SQLite persistence
  dashboard/
    index.html         # Built-in web dashboard
```

## Roadmap

- [ ] Streaming support (real-time cost tracking via proxy mode)
- [ ] Anomaly detection (alert on unusual spend spikes)
- [ ] Model optimization suggestions ("Switch 30% to GPT-4o-mini, save $X/month")
- [ ] Slack/webhook alerts
- [ ] Multi-team budget allocation
- [ ] Direct API integration (OpenAI Usage API, Anthropic Admin API)

## License

MIT
