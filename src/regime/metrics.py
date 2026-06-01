from __future__ import annotations

import pandas as pd


def prepare_prices(prices: pd.DataFrame) -> pd.DataFrame:
    if prices.empty:
        return pd.DataFrame()
    df = prices.copy().sort_values("trade_date").reset_index(drop=True)
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    if "high" not in df.columns:
        df["high"] = df["close"]
    df["high"] = pd.to_numeric(df["high"], errors="coerce").fillna(df["close"])
    return df.dropna(subset=["trade_date", "close"])


def period_return(close: pd.Series, days: int) -> float:
    if len(close) <= days:
        return 0.0
    start = close.iloc[-days - 1]
    if not start:
        return 0.0
    return float(close.iloc[-1] / start - 1)


def rolling_volatility(close: pd.Series, window: int = 20) -> pd.Series:
    return close.pct_change().rolling(window).std()


def volatility_percentile(close: pd.Series, window: int = 20) -> float:
    vol = rolling_volatility(close, window).dropna()
    if vol.empty:
        return 0.0
    latest = vol.iloc[-1]
    return float((vol <= latest).mean())


def drawdown_from_high(close: pd.Series, window: int = 60) -> float:
    if close.empty:
        return 0.0
    high = close.tail(window).max()
    if not high:
        return 0.0
    return float(close.iloc[-1] / high - 1)
