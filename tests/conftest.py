import os
from datetime import date, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from token_forecast.models import UsageRecord

# Use in-memory DB for tests
os.environ["TOKEN_FORECAST_DB_PATH"] = ":memory:"


@pytest.fixture
def sample_records() -> list[UsageRecord]:
    """Generate 30 days of realistic usage data."""
    records = []
    start = date(2025, 3, 1)
    for i in range(30):
        d = start + timedelta(days=i)
        records.append(
            UsageRecord(
                date=d,
                model="gpt-4o",
                provider="openai",
                input_tokens=50000 + i * 1000,
                output_tokens=20000 + i * 500,
                cost=1.50 + i * 0.05,
                requests_count=30 + i,
            )
        )
        records.append(
            UsageRecord(
                date=d,
                model="claude-sonnet-4-20250514",
                provider="anthropic",
                input_tokens=30000 + i * 800,
                output_tokens=15000 + i * 400,
                cost=0.80 + i * 0.03,
                requests_count=20 + i,
            )
        )
    return records


@pytest.fixture
def sample_csv_content() -> bytes:
    """Generate a valid CSV as bytes."""
    lines = ["date,model,provider,input_tokens,output_tokens,cost,requests"]
    start = date(2025, 3, 1)
    for i in range(30):
        d = start + timedelta(days=i)
        lines.append(
            f"{d},gpt-4o,openai,{50000 + i * 1000},{20000 + i * 500},{1.5 + i * 0.05:.2f},{30 + i}"
        )
    return "\n".join(lines).encode("utf-8")


@pytest.fixture
async def client():
    """Async test client for the FastAPI app."""
    from token_forecast.api.app import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
