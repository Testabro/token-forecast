from datetime import date

import pytest

from token_forecast.parsers.csv_parser import parse_csv
from token_forecast.parsers.pricing import detect_provider, estimate_cost


class TestCSVParser:
    def test_parse_generic_format(self, sample_csv_content):
        records = parse_csv(sample_csv_content)
        assert len(records) == 30
        assert records[0].model == "gpt-4o"
        assert records[0].provider == "openai"
        assert records[0].date == date(2025, 3, 1)

    def test_parse_minimal_csv(self):
        csv = "date,cost\n2025-03-01,10.50\n2025-03-02,12.30"
        records = parse_csv(csv)
        assert len(records) == 2
        assert records[0].cost == 10.50
        assert records[1].cost == 12.30

    def test_missing_date_column_raises(self):
        csv = "model,cost\ngpt-4o,10.50"
        with pytest.raises(ValueError, match="date"):
            parse_csv(csv)

    def test_missing_cost_and_tokens_raises(self):
        csv = "date,model\n2025-03-01,gpt-4o"
        with pytest.raises(ValueError, match="cost.*token"):
            parse_csv(csv)

    def test_empty_csv_raises(self):
        with pytest.raises(ValueError):
            parse_csv("")

    def test_cost_from_tokens(self):
        csv = "date,model,input_tokens,output_tokens\n2025-03-01,gpt-4o,1000000,500000"
        records = parse_csv(csv)
        assert records[0].cost > 0  # Should estimate from pricing

    def test_date_format_slash(self):
        csv = "date,cost\n03/15/2025,5.00"
        records = parse_csv(csv)
        assert records[0].date == date(2025, 3, 15)

    def test_bytes_with_bom(self):
        csv = b"\xef\xbb\xbfdate,cost\n2025-03-01,10.00"
        records = parse_csv(csv)
        assert len(records) == 1


class TestPricing:
    def test_estimate_gpt4o(self):
        cost = estimate_cost("gpt-4o", 1_000_000, 500_000)
        assert cost == pytest.approx(7.50, abs=0.01)

    def test_estimate_unknown_model_uses_fallback(self):
        cost = estimate_cost("totally-unknown-model", 1_000_000, 0)
        assert cost > 0  # Should use fallback pricing

    def test_detect_openai_provider(self):
        assert detect_provider("gpt-4o") == "openai"
        assert detect_provider("gpt-3.5-turbo") == "openai"

    def test_detect_anthropic_provider(self):
        assert detect_provider("claude-sonnet-4-20250514") == "anthropic"

    def test_detect_unknown_provider(self):
        assert detect_provider("llama-3.1-70b") == "unknown"
