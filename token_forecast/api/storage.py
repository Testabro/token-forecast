import os
from datetime import date

import aiosqlite

from token_forecast.config import settings
from token_forecast.models import UsageRecord

_SCHEMA = """
CREATE TABLE IF NOT EXISTS usage_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    model TEXT NOT NULL DEFAULT 'unknown',
    provider TEXT NOT NULL DEFAULT 'unknown',
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    cost REAL NOT NULL DEFAULT 0.0,
    requests_count INTEGER NOT NULL DEFAULT 1,
    tag TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_usage_date ON usage_records(date);
CREATE INDEX IF NOT EXISTS idx_usage_model ON usage_records(model);
"""


async def _get_db() -> aiosqlite.Connection:
    os.makedirs(os.path.dirname(settings.db_path) or ".", exist_ok=True)
    db = await aiosqlite.connect(settings.db_path)
    db.row_factory = aiosqlite.Row
    await db.executescript(_SCHEMA)
    return db


async def store_records(records: list[UsageRecord]) -> int:
    db = await _get_db()
    try:
        await db.executemany(
            """INSERT INTO usage_records (date, model, provider, input_tokens, output_tokens, cost, requests_count, tag)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    r.date.isoformat(),
                    r.model,
                    r.provider,
                    r.input_tokens,
                    r.output_tokens,
                    r.cost,
                    r.requests_count,
                    r.tag,
                )
                for r in records
            ],
        )
        await db.commit()
        return len(records)
    finally:
        await db.close()


async def get_records(
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[UsageRecord]:
    db = await _get_db()
    try:
        query = "SELECT * FROM usage_records"
        params: list = []
        conditions = []
        if start_date:
            conditions.append("date >= ?")
            params.append(start_date.isoformat())
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date.isoformat())
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY date DESC"

        rows = await db.execute_fetchall(query, params)
        return [
            UsageRecord(
                date=date.fromisoformat(row["date"]),
                model=row["model"],
                provider=row["provider"],
                input_tokens=row["input_tokens"],
                output_tokens=row["output_tokens"],
                cost=row["cost"],
                requests_count=row["requests_count"],
                tag=row["tag"],
            )
            for row in rows
        ]
    finally:
        await db.close()


async def set_setting(key: str, value: str) -> None:
    db = await _get_db()
    try:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        await db.commit()
    finally:
        await db.close()


async def get_setting(key: str, default: str = "") -> str:
    db = await _get_db()
    try:
        row = await db.execute_fetchall(
            "SELECT value FROM settings WHERE key = ?", (key,)
        )
        return row[0]["value"] if row else default
    finally:
        await db.close()


async def clear_records() -> None:
    db = await _get_db()
    try:
        await db.execute("DELETE FROM usage_records")
        await db.commit()
    finally:
        await db.close()
