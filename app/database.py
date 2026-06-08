from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from app.config import ensure_directories, settings
from app.report_generator import today_string

if TYPE_CHECKING:
    from app.analyzer import StockAnalysis


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS scan_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_date TEXT NOT NULL,
    stock_code TEXT NOT NULL,
    last_price REAL,
    daily_change REAL,
    score INTEGER,
    status TEXT,
    rsi REAL,
    volume_ratio REAL,
    macd_status TEXT,
    trend_status TEXT,
    entry_low REAL,
    entry_high REAL,
    stop_loss REAL,
    target_1 REAL,
    target_2 REAL,
    risk_reward REAL,
    reasons TEXT,
    created_at TEXT NOT NULL
);
"""


def get_connection() -> sqlite3.Connection:
    ensure_directories()
    connection = sqlite3.connect(settings.database_path)
    connection.execute(CREATE_TABLE_SQL)
    return connection


def save_scan_results(results: list[StockAnalysis]) -> int:
    if not results:
        return 0

    created_at = datetime.now(ZoneInfo(settings.timezone)).isoformat(timespec="seconds")
    rows = [
        (
            today_string(),
            item.stock_code,
            item.last_price,
            item.daily_change,
            item.score,
            item.status,
            item.rsi,
            item.volume_ratio,
            item.macd_status,
            item.trend_status,
            item.entry_low,
            item.entry_high,
            item.stop_loss,
            item.target_1,
            item.target_2,
            item.risk_reward,
            "; ".join(item.reasons),
            created_at,
        )
        for item in results
    ]

    with get_connection() as connection:
        connection.executemany(
            """
            INSERT INTO scan_results (
                scan_date, stock_code, last_price, daily_change, score, status,
                rsi, volume_ratio, macd_status, trend_status, entry_low, entry_high,
                stop_loss, target_1, target_2, risk_reward, reasons, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        connection.commit()
    return len(rows)
