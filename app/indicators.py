from __future__ import annotations

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import AverageTrueRange


def add_technical_indicators(data: pd.DataFrame) -> pd.DataFrame:
    df = data.copy()

    for window in (5, 10, 20, 50, 100, 200):
        df[f"MA{window}"] = df["Close"].rolling(window=window).mean()

    df["EMA12"] = df["Close"].ewm(span=12, adjust=False).mean()
    df["EMA26"] = df["Close"].ewm(span=26, adjust=False).mean()

    df["RSI14"] = RSIIndicator(close=df["Close"], window=14).rsi()

    macd = MACD(close=df["Close"], window_fast=12, window_slow=26, window_sign=9)
    df["MACD"] = macd.macd()
    df["MACD_Signal"] = macd.macd_signal()
    df["MACD_Histogram"] = macd.macd_diff()

    df["Volume_MA20"] = df["Volume"].rolling(window=20).mean()
    df["Volume_Ratio"] = df["Volume"] / df["Volume_MA20"]

    # Shifted one day so today's breakout is compared with prior resistance.
    df["Support_20"] = df["Low"].rolling(window=20).min().shift(1)
    df["Resistance_20"] = df["High"].rolling(window=20).max().shift(1)

    atr = AverageTrueRange(high=df["High"], low=df["Low"], close=df["Close"], window=14)
    df["ATR14"] = atr.average_true_range()

    df["Daily_Change_Pct"] = df["Close"].pct_change() * 100
    df["Weekly_Change_Pct"] = df["Close"].pct_change(5) * 100
    df["Monthly_Change_Pct"] = df["Close"].pct_change(20) * 100

    df["MACD_Golden_Cross"] = (
        (df["MACD"] > df["MACD_Signal"])
        & (df["MACD"].shift(1) <= df["MACD_Signal"].shift(1))
    )

    return df

