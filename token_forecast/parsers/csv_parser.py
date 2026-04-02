import csv
import io
from datetime import date, datetime

from token_forecast.models import UsageRecord
from token_forecast.parsers.pricing import detect_provider, estimate_cost

# Known column name mappings
COLUMN_ALIASES = {
    "date": ["date", "timestamp", "day", "time", "created_at"],
    "model": ["model", "model_name", "model_id", "engine"],
    "provider": ["provider", "organization", "source"],
    "input_tokens": ["input_tokens", "prompt_tokens", "tokens_in", "input"],
    "output_tokens": ["output_tokens", "completion_tokens", "tokens_out", "output"],
    "cost": ["cost", "total_cost", "amount", "price", "usd", "spend"],
    "requests_count": ["requests", "requests_count", "count", "num_requests", "api_calls"],
    "tag": ["tag", "label", "feature", "team", "project"],
}


def _normalize_columns(headers: list[str]) -> dict[str, str]:
    """Map actual CSV column names to our canonical field names."""
    mapping = {}
    headers_lower = [h.strip().lower().replace(" ", "_") for h in headers]
    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in headers_lower:
                idx = headers_lower.index(alias)
                mapping[field] = headers[idx].strip()
                break
    return mapping


def _parse_date(value: str) -> date:
    """Parse date from various formats."""
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y/%m/%d", "%d-%m-%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {value}")


def parse_csv(content: str | bytes) -> list[UsageRecord]:
    """Parse a CSV string/bytes into UsageRecord objects.

    Auto-detects column format from headers. Minimum required: date + (cost OR token columns).
    """
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig")  # Handle BOM

    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise ValueError("CSV file is empty or has no headers")

    col_map = _normalize_columns(list(reader.fieldnames))

    if "date" not in col_map:
        raise ValueError("CSV must have a 'date' column")

    has_cost = "cost" in col_map
    has_tokens = "input_tokens" in col_map or "output_tokens" in col_map
    if not has_cost and not has_tokens:
        raise ValueError(
            "CSV must have a 'cost' column or token columns (input_tokens, output_tokens)"
        )

    records = []
    for row in reader:
        try:
            record_date = _parse_date(row[col_map["date"]])
        except (ValueError, KeyError):
            continue

        model = row.get(col_map.get("model", ""), "unknown").strip() or "unknown"
        provider = row.get(col_map.get("provider", ""), "").strip()
        if not provider:
            provider = detect_provider(model)

        input_tokens = int(float(row.get(col_map.get("input_tokens", ""), "0") or "0"))
        output_tokens = int(float(row.get(col_map.get("output_tokens", ""), "0") or "0"))

        cost_str = row.get(col_map.get("cost", ""), "0") or "0"
        cost = float(cost_str.replace("$", "").replace(",", "").strip())
        if cost == 0 and has_tokens:
            cost = estimate_cost(model, input_tokens, output_tokens)

        requests_count = int(float(row.get(col_map.get("requests_count", ""), "1") or "1"))
        tag = row.get(col_map.get("tag", ""), None)

        records.append(
            UsageRecord(
                date=record_date,
                model=model,
                provider=provider,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                requests_count=requests_count,
                tag=tag if tag else None,
            )
        )

    if not records:
        raise ValueError("No valid records found in CSV")

    return records
