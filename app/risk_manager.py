from __future__ import annotations

import math
from typing import Any

import pandas as pd


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(parsed):
        return default
    return parsed


def calculate_trade_plan(row: pd.Series, breakout: bool) -> dict[str, float | str | list[str]]:
    close = _as_float(row.get("Close"))
    ma5 = _as_float(row.get("MA5"), close)
    support = _as_float(row.get("Support_20"))
    atr = _as_float(row.get("ATR14"))

    if breakout:
        entry_low = close
        entry_high = close * 1.01
    else:
        entry_low = min(close, ma5)
        entry_high = close

    atr_stop = close - (1.5 * atr)
    stop_candidates = [value for value in (support, atr_stop) if value > 0]
    stop_loss = min(stop_candidates) if stop_candidates else close * 0.95

    risk = entry_high - stop_loss
    warnings: list[str] = []
    if risk <= 0:
        risk = max(entry_high * 0.03, 1.0)
        stop_loss = entry_high - risk
        warnings.append("Stop loss disesuaikan karena risk awal tidak valid")

    target_1 = entry_high + (2 * risk)
    target_2 = entry_high + (3 * risk)
    risk_reward = (target_1 - entry_high) / risk if risk > 0 else 0

    risk_pct = (risk / entry_high) * 100 if entry_high else 0
    if risk_reward < 1.5:
        warnings.append("Risk reward kurang sehat")
    if risk_pct > 10:
        warnings.append("Jarak stop loss lebih dari 10%, posisi perlu diperkecil")

    return {
        "entry_low": entry_low,
        "entry_high": entry_high,
        "stop_loss": stop_loss,
        "target_1": target_1,
        "target_2": target_2,
        "risk_reward": risk_reward,
        "warnings": warnings,
    }

