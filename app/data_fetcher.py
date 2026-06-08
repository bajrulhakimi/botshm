from __future__ import annotations

from pathlib import Path

import pandas as pd
import yfinance as yf

from app.config import settings


PRICE_COLUMNS = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]


def load_stock_codes(csv_path: Path | None = None) -> list[str]:
    path = csv_path or settings.stocks_csv
    if not path.exists():
        raise FileNotFoundError(f"File daftar saham tidak ditemukan: {path}")

    rows = pd.read_csv(path, header=None, dtype=str).fillna("")
    codes: list[str] = []
    for value in rows.iloc[:, 0].tolist():
        code = str(value).strip().upper()
        if not code or code == "CODE":
            continue
        codes.append(code.replace(".JK", ""))
    return list(dict.fromkeys(codes))


def to_yfinance_symbol(code: str) -> str:
    clean_code = code.strip().upper()
    if clean_code.endswith(".JK"):
        return clean_code
    return f"{clean_code}.JK"


def _flatten_yfinance_columns(data: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(data.columns, pd.MultiIndex):
        return data

    renamed_columns = []
    for column in data.columns:
        selected = next((part for part in column if part in PRICE_COLUMNS), column[0])
        renamed_columns.append(selected)
    data = data.copy()
    data.columns = renamed_columns
    return data.loc[:, ~data.columns.duplicated()]


def fetch_daily_prices(code: str, period: str | None = None) -> pd.DataFrame:
    symbol = to_yfinance_symbol(code)
    try:
        data = yf.download(
            symbol,
            period=period or settings.yfinance_period,
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )
    except Exception as exc:
        raise RuntimeError(f"Gagal mengambil data {symbol}: {exc}") from exc

    if data.empty:
        return pd.DataFrame()

    data = _flatten_yfinance_columns(data)
    available_columns = [column for column in PRICE_COLUMNS if column in data.columns]
    data = data[available_columns].copy()
    data = data.dropna(subset=["High", "Low", "Close", "Volume"], how="any")
    data.index = pd.to_datetime(data.index)
    data.sort_index(inplace=True)
    return data

