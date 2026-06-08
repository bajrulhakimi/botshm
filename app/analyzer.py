from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import isnan
from typing import Any

import pandas as pd

from app.config import settings
from app.data_fetcher import fetch_daily_prices, load_stock_codes
from app.indicators import add_technical_indicators
from app.risk_manager import calculate_trade_plan
from app.scoring import build_rsi_note, calculate_score, classify_score


ESSENTIAL_COLUMNS = [
    "Close",
    "MA20",
    "MA50",
    "RSI14",
    "MACD",
    "MACD_Signal",
    "Volume_MA20",
    "Volume_Ratio",
    "Support_20",
    "Resistance_20",
    "ATR14",
    "Daily_Change_Pct",
]


@dataclass
class StockAnalysis:
    stock_code: str
    last_price: float
    daily_change: float
    weekly_change: float
    monthly_change: float
    score: int
    status: str
    rsi: float
    volume_ratio: float
    macd_status: str
    trend_status: str
    entry_low: float
    entry_high: float
    stop_loss: float
    target_1: float
    target_2: float
    risk_reward: float
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    breakout: bool = False
    support_20: float = 0.0
    resistance_20: float = 0.0
    distance_to_support_pct: float = 0.0
    distance_to_resistance_pct: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean_float(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if isnan(parsed):
        return default
    return parsed


def _has_complete_data(row: pd.Series) -> bool:
    for column in ESSENTIAL_COLUMNS:
        value = row.get(column)
        if value is None or pd.isna(value):
            return False
    return True


def _is_breakout(row: pd.Series) -> bool:
    close = _clean_float(row.get("Close"))
    resistance = _clean_float(row.get("Resistance_20"))
    volume_ratio = _clean_float(row.get("Volume_Ratio"))
    daily_change = _clean_float(row.get("Daily_Change_Pct"))
    return close > resistance > 0 and volume_ratio > 1.5 and daily_change >= 1


def _trend_status(row: pd.Series) -> str:
    close = _clean_float(row.get("Close"))
    ma20 = _clean_float(row.get("MA20"))
    ma50 = _clean_float(row.get("MA50"))
    ma100 = _clean_float(row.get("MA100"))
    ma200 = _clean_float(row.get("MA200"))

    if close > ma20 > ma50 > 0 and ma50 > ma100 > 0 and close > ma200 > 0:
        return "Bullish Kuat"
    if close > ma20 > 0 and close > ma50 > 0 and ma20 > ma50:
        return "Bullish"
    if close < ma50 and close < ma100:
        return "Bearish"
    return "Netral"


def _macd_status(row: pd.Series) -> str:
    macd = _clean_float(row.get("MACD"))
    signal = _clean_float(row.get("MACD_Signal"))
    histogram = _clean_float(row.get("MACD_Histogram"))
    golden_cross = bool(row.get("MACD_Golden_Cross", False))
    if golden_cross:
        return "Golden Cross"
    if macd > signal and histogram > 0:
        return "Positif"
    return "Negatif"


def _risk_warnings(row: pd.Series) -> list[str]:
    warnings: list[str] = []
    close = _clean_float(row.get("Close"))
    ma50 = _clean_float(row.get("MA50"))
    ma100 = _clean_float(row.get("MA100"))
    rsi = _clean_float(row.get("RSI14"))
    volume_ratio = _clean_float(row.get("Volume_Ratio"))
    volume_ma20 = _clean_float(row.get("Volume_MA20"))
    atr = _clean_float(row.get("ATR14"))
    daily_change = _clean_float(row.get("Daily_Change_Pct"))

    if volume_ma20 and volume_ma20 < settings.min_average_volume:
        warnings.append("Volume rata-rata relatif kecil")
    if close and atr and (atr / close) * 100 > 7:
        warnings.append("Volatilitas harga tinggi")
    if rsi > 80:
        warnings.append("RSI di atas 80, risiko overbought")
    if close < ma50 and close < ma100:
        warnings.append("Harga berada di bawah MA50 dan MA100")
    if volume_ratio < 0.7:
        warnings.append("Volume ratio terlalu kecil")
    if daily_change < -7:
        warnings.append("Harga turun tajam lebih dari 7% dalam sehari")

    return warnings


def analyze_stock(code: str) -> StockAnalysis | None:
    normalized_code = code.strip().upper().replace(".JK", "")
    data = fetch_daily_prices(normalized_code)
    if data.empty:
        print(f"{normalized_code}: data kosong, dilewati.")
        return None
    if len(data) < settings.min_candles:
        print(f"{normalized_code}: data kurang dari {settings.min_candles} candle, dilewati.")
        return None

    data = add_technical_indicators(data)
    latest = data.iloc[-1]
    if not _has_complete_data(latest):
        print(f"{normalized_code}: data indikator belum lengkap, dilewati.")
        return None

    breakout = _is_breakout(latest)
    score, reasons = calculate_score(latest, breakout)
    warnings = _risk_warnings(latest)
    rsi_note = build_rsi_note(latest)
    if rsi_note not in reasons:
        reasons.append(rsi_note)

    plan = calculate_trade_plan(latest, breakout)
    warnings.extend(plan.get("warnings", []))

    close = _clean_float(latest.get("Close"))
    support = _clean_float(latest.get("Support_20"))
    resistance = _clean_float(latest.get("Resistance_20"))
    distance_to_support = ((close - support) / close) * 100 if close and support else 0
    distance_to_resistance = ((resistance - close) / close) * 100 if close and resistance else 0

    return StockAnalysis(
        stock_code=normalized_code,
        last_price=close,
        daily_change=_clean_float(latest.get("Daily_Change_Pct")),
        weekly_change=_clean_float(latest.get("Weekly_Change_Pct")),
        monthly_change=_clean_float(latest.get("Monthly_Change_Pct")),
        score=score,
        status=classify_score(score),
        rsi=_clean_float(latest.get("RSI14")),
        volume_ratio=_clean_float(latest.get("Volume_Ratio")),
        macd_status=_macd_status(latest),
        trend_status=_trend_status(latest),
        entry_low=_clean_float(plan["entry_low"]),
        entry_high=_clean_float(plan["entry_high"]),
        stop_loss=_clean_float(plan["stop_loss"]),
        target_1=_clean_float(plan["target_1"]),
        target_2=_clean_float(plan["target_2"]),
        risk_reward=_clean_float(plan["risk_reward"]),
        reasons=reasons,
        warnings=list(dict.fromkeys(warnings)),
        breakout=breakout,
        support_20=support,
        resistance_20=resistance,
        distance_to_support_pct=distance_to_support,
        distance_to_resistance_pct=distance_to_resistance,
    )


def scan_all_stocks() -> list[StockAnalysis]:
    results: list[StockAnalysis] = []
    codes = load_stock_codes()
    if not codes:
        print("Daftar saham kosong.")
        return results

    for code in codes:
        try:
            result = analyze_stock(code)
            if result:
                results.append(result)
                print(f"{result.stock_code}: selesai, skor {result.score}/100")
        except Exception as exc:
            print(f"{code}: gagal dianalisa, lanjut ke saham berikutnya. Detail: {exc}")

    results.sort(key=lambda item: item.score, reverse=True)
    return results

