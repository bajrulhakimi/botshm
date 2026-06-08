from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _get_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default)).strip()
    try:
        return int(raw_value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    base_dir: Path = BASE_DIR
    data_dir: Path = BASE_DIR / "data"
    reports_dir: Path = BASE_DIR / "reports"
    logs_dir: Path = BASE_DIR / "logs"
    stocks_csv: Path = BASE_DIR / "data" / "stocks.csv"
    watchlist_csv: Path = BASE_DIR / "data" / "watchlist.csv"
    database_path: Path = BASE_DIR / "data" / "scan_results.sqlite3"
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    min_score: int = _get_int("MIN_SCORE", 65)
    top_n: int = _get_int("TOP_N", 10)
    scan_time: str = os.getenv("SCAN_TIME", "16:30").strip() or "16:30"
    timezone: str = os.getenv("TIMEZONE", "Asia/Jakarta").strip() or "Asia/Jakarta"
    yfinance_period: str = os.getenv("YFINANCE_PERIOD", "2y").strip() or "2y"
    min_candles: int = _get_int("MIN_CANDLES", 100)
    min_average_volume: int = _get_int("MIN_AVERAGE_VOLUME", 100_000)


settings = Settings()


def ensure_directories() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    settings.logs_dir.mkdir(parents=True, exist_ok=True)

