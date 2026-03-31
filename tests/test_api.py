import io

import pytest


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health(self, client):
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"


class TestUploadEndpoint:
    @pytest.mark.asyncio
    async def test_upload_valid_csv(self, client, sample_csv_content):
        files = {"file": ("usage.csv", io.BytesIO(sample_csv_content), "text/csv")}
        res = await client.post("/api/upload", files=files)
        assert res.status_code == 200
        data = res.json()
        assert data["records_imported"] == 30
        assert "gpt-4o" in data["models_found"]

    @pytest.mark.asyncio
    async def test_upload_non_csv_rejected(self, client):
        files = {"file": ("data.txt", io.BytesIO(b"not a csv"), "text/plain")}
        res = await client.post("/api/upload", files=files)
        assert res.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_invalid_csv_rejected(self, client):
        bad_csv = b"name,age\nAlice,30"
        files = {"file": ("bad.csv", io.BytesIO(bad_csv), "text/csv")}
        res = await client.post("/api/upload", files=files)
        assert res.status_code == 400


class TestBudgetEndpoint:
    @pytest.mark.asyncio
    async def test_set_budget(self, client):
        res = await client.post("/api/budget", json={"amount": 5000})
        assert res.status_code == 200
        assert res.json()["budget_monthly"] == 5000

    @pytest.mark.asyncio
    async def test_negative_budget_rejected(self, client):
        res = await client.post("/api/budget", json={"amount": -100})
        assert res.status_code == 400


class TestDashboardEndpoint:
    @pytest.mark.asyncio
    async def test_dashboard_returns_html(self, client):
        res = await client.get("/dashboard")
        assert res.status_code == 200
        assert "Token Forecast" in res.text


class TestSummaryEndpoint:
    @pytest.mark.asyncio
    async def test_summary_empty(self, client):
        res = await client.get("/api/summary")
        assert res.status_code == 200
        assert res.json()["total_cost"] == 0
