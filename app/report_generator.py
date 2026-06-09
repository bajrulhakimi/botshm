from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

import pandas as pd

from app.config import ensure_directories, settings
from app.stock_universe import (
    DEFAULT_GROUP,
    format_group_label,
    load_group_symbols,
    normalize_group_name,
)

if TYPE_CHECKING:
    from app.analyzer import StockAnalysis


DISCLAIMER = (
    "Analisa ini hanya alat bantu screening, bukan rekomendasi beli/jual. "
    "Risiko ditanggung masing-masing investor."
)

DATA_LIMITATION = (
    "Data dari yfinance bisa delay, bukan data broker summary, bukan orderbook "
    "real-time, dan bukan data net buy/net sell sekuritas. Cocok untuk screening "
    "harian, bukan scalping real-time."
)


def today_string() -> str:
    return datetime.now(ZoneInfo(settings.timezone)).strftime("%Y-%m-%d")


def format_price(value: float | int | None) -> str:
    if value is None:
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    if pd.isna(number):
        return "-"
    if abs(number) >= 100:
        return f"{number:,.0f}".replace(",", ".")
    return f"{number:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def format_pct(value: float | int | None) -> str:
    if value is None:
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    if pd.isna(number):
        return "-"
    sign = "+" if number > 0 else ""
    return f"{sign}{number:.2f}%"


def format_ratio(value: float | int | None) -> str:
    if value is None:
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    if pd.isna(number):
        return "-"
    return f"{number:.2f}x"


def format_risk_reward(value: float | int | None) -> str:
    if value is None:
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    if pd.isna(number) or number <= 0:
        return "-"
    return f"1:{number:.2f}"


def generate_text_report(
    results: list[StockAnalysis],
    top_n: int | None = None,
    group_name: str = DEFAULT_GROUP,
) -> str:
    shown_results = results[:top_n] if top_n else results
    try:
        universe_size = len(load_group_symbols(group_name))
    except (FileNotFoundError, ValueError):
        universe_size = len(results)
    lines: list[str] = [
        "HASIL SCREENING SAHAM IDX",
        f"Group: {format_group_label(group_name)}",
        f"Jumlah saham dalam group: {universe_size}",
        f"Berhasil dianalisa: {len(results)}",
        f"Tanggal: {today_string()}",
        "Sumber data: Yahoo Finance / yfinance",
        "Catatan: Data bukan real-time resmi IDX.",
        f"Batasan data gratis: {DATA_LIMITATION}",
        "",
    ]

    if not shown_results:
        lines.append("Tidak ada saham yang berhasil dianalisa.")
    for index, item in enumerate(shown_results, start=1):
        lines.extend(
            [
                f"{index}. {item.stock_code}",
                f"Skor: {item.score}/100",
                f"Status: {item.status}",
                f"Harga Terakhir: {format_price(item.last_price)}",
                f"Perubahan Harian: {format_pct(item.daily_change)}",
                f"Perubahan Mingguan: {format_pct(item.weekly_change)}",
                f"Perubahan Bulanan: {format_pct(item.monthly_change)}",
                f"Volume Ratio: {format_ratio(item.volume_ratio)}",
                f"RSI: {item.rsi:.2f}",
                f"MACD: {item.macd_status}",
                f"Trend: {item.trend_status}",
                f"Support 20H: {format_price(item.support_20)}",
                f"Resistance 20H: {format_price(item.resistance_20)}",
                f"Jarak ke Support: {format_pct(item.distance_to_support_pct)}",
                f"Jarak ke Resistance: {format_pct(item.distance_to_resistance_pct)}",
                f"Entry Area: {format_price(item.entry_low)} - {format_price(item.entry_high)}",
                f"Stop Loss: {format_price(item.stop_loss)}",
                f"Target 1: {format_price(item.target_1)}",
                f"Target 2: {format_price(item.target_2)}",
                f"Risk Reward: {format_risk_reward(item.risk_reward)}",
                "Alasan:",
            ]
        )
        lines.extend(f"- {reason}" for reason in item.reasons)
        if item.warnings:
            lines.append("Peringatan:")
            lines.extend(f"- {warning}" for warning in item.warnings)
        lines.append("")

    lines.extend(["Disclaimer:", DISCLAIMER])
    return "\n".join(lines).strip() + "\n"


def _safe_group_name(group_name: str) -> str:
    return normalize_group_name(group_name).replace("_", "-")


def save_text_report(
    results: list[StockAnalysis],
    top_n: int | None = None,
    group_name: str = DEFAULT_GROUP,
) -> Path:
    ensure_directories()
    path = settings.reports_dir / f"report_{_safe_group_name(group_name)}_{today_string()}.txt"
    path.write_text(
        generate_text_report(results, top_n=top_n, group_name=group_name),
        encoding="utf-8",
    )
    return path


def export_csv(results: list[StockAnalysis], group_name: str = DEFAULT_GROUP) -> Path:
    ensure_directories()
    path = settings.reports_dir / f"screening_{_safe_group_name(group_name)}_{today_string()}.csv"
    records = [item.to_dict() for item in results]
    frame = pd.DataFrame(records)
    if not frame.empty:
        frame.insert(0, "group", normalize_group_name(group_name))
        frame["reasons"] = frame["reasons"].apply(lambda values: "; ".join(values))
        frame["warnings"] = frame["warnings"].apply(lambda values: "; ".join(values))
    frame.to_csv(path, index=False)
    return path
