from __future__ import annotations

from math import isnan
from typing import Any

import pandas as pd


def _value(row: pd.Series, key: str, default: float = 0.0) -> float:
    value = row.get(key, default)
    try:
        value = float(value)
    except (TypeError, ValueError):
        return default
    if isnan(value):
        return default
    return value


def classify_score(score: int) -> str:
    if score >= 85:
        return "Sangat Kuat Dipantau"
    if score >= 75:
        return "Menarik Dipantau"
    if score >= 65:
        return "Watchlist"
    if score >= 50:
        return "Netral"
    return "Belum Menarik"


def calculate_score(row: pd.Series, breakout: bool) -> tuple[int, list[str]]:
    close = _value(row, "Close")
    ma5 = _value(row, "MA5")
    ma20 = _value(row, "MA20")
    ma50 = _value(row, "MA50")
    ma200 = _value(row, "MA200")
    volume_ratio = _value(row, "Volume_Ratio")
    rsi = _value(row, "RSI14")
    macd = _value(row, "MACD")
    macd_signal = _value(row, "MACD_Signal")
    daily_change = _value(row, "Daily_Change_Pct")
    golden_cross = bool(row.get("MACD_Golden_Cross", False))

    score = 0
    reasons: list[str] = []

    if close > ma20 > 0:
        score += 10
        reasons.append("Harga berada di atas MA20")
    if close > ma50 > 0:
        score += 10
        reasons.append("Harga berada di atas MA50")
    if ma5 > ma20 > 0:
        score += 10
        reasons.append("MA5 berada di atas MA20")
    if ma20 > ma50 > 0:
        score += 10
        reasons.append("MA20 berada di atas MA50")
    if close > ma200 > 0:
        score += 5
        reasons.append("Harga berada di atas MA200")
    if breakout:
        score += 20
        reasons.append("Breakout resistance 20 hari dengan konfirmasi volume")
    if volume_ratio > 1.5:
        score += 15
        reasons.append("Volume lebih besar dari 1,5x rata-rata 20 hari")
    if volume_ratio > 2.0:
        score += 5
        reasons.append("Volume sangat kuat, di atas 2x rata-rata 20 hari")
    if 45 <= rsi <= 70:
        score += 10
        reasons.append("RSI berada di area sehat")
    if macd > macd_signal:
        score += 10
        reasons.append("MACD berada di atas signal")
    if golden_cross:
        score += 5
        reasons.append("MACD baru golden cross")

    if rsi > 80:
        score -= 15
        reasons.append("Penalty: RSI di atas 80, risiko overbought")
    if volume_ratio < 0.7:
        score -= 10
        reasons.append("Penalty: volume ratio di bawah 0,7")
    if close < ma50:
        score -= 10
        reasons.append("Penalty: harga di bawah MA50")
    if daily_change < -7:
        score -= 15
        reasons.append("Penalty: harga turun harian lebih dari 7%")

    score = max(0, min(100, score))
    return int(score), reasons


def build_rsi_note(row: pd.Series) -> str:
    rsi = _value(row, "RSI14")
    if 45 <= rsi <= 70:
        return "RSI sehat"
    if 30 <= rsi < 45:
        return "RSI potensi rebound, tetapi belum kuat"
    if rsi < 30:
        return "RSI oversold, rebound berisiko tinggi"
    if 70 < rsi <= 80:
        return "RSI mulai panas"
    if rsi > 80:
        return "RSI overbought"
    return "RSI netral"

