import pytest

from token_forecast.forecast.engine import check_budget, forecast_cost
from token_forecast.models import BudgetAlert, ForecastResult


class TestForecastCost:
    def test_returns_correct_days(self, sample_records):
        results = forecast_cost(sample_records, days=14)
        assert len(results) == 14

    def test_returns_forecast_result_objects(self, sample_records):
        results = forecast_cost(sample_records, days=7)
        for r in results:
            assert isinstance(r, ForecastResult)
            assert r.predicted_cost >= 0
            assert r.lower_bound <= r.predicted_cost
            assert r.upper_bound >= r.predicted_cost

    def test_empty_records_raises(self):
        with pytest.raises(ValueError, match="No usage records"):
            forecast_cost([], days=7)

    def test_insufficient_data_raises(self, sample_records):
        with pytest.raises(ValueError, match="at least 3 days"):
            forecast_cost(sample_records[:2], days=7)


class TestCheckBudget:
    def test_on_track(self, sample_records):
        forecast = [
            ForecastResult(
                date=sample_records[-1].date,
                predicted_cost=1.0,
                lower_bound=0.5,
                upper_bound=1.5,
            )
        ]
        alert = check_budget(sample_records, forecast, monthly_budget=100000)
        assert alert.status == "on_track"

    def test_critical_when_over_budget(self, sample_records):
        forecast = [
            ForecastResult(
                date=sample_records[-1].date,
                predicted_cost=500.0,
                lower_bound=400.0,
                upper_bound=600.0,
            )
            for _ in range(30)
        ]
        alert = check_budget(sample_records, forecast, monthly_budget=10)
        assert alert.status == "critical"

    def test_no_budget_returns_on_track(self, sample_records):
        alert = check_budget(sample_records, [], monthly_budget=0)
        assert alert.status == "on_track"
        assert "No budget" in alert.message
