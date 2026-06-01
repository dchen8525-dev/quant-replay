from __future__ import annotations

import pandas as pd

FACTOR_NAMES = [
    "momentum_5d",
    "momentum_20d",
    "momentum_60d",
    "volatility_20d",
    "volume_ratio_5d",
    "ma_distance_20d",
    "drawdown_from_60d_high",
    "turnover_proxy",
]


def calculate_factors(prices: pd.DataFrame) -> dict[str, float]:
    if prices.empty or "close" not in prices.columns:
        return {name: 0.0 for name in FACTOR_NAMES}

    df = prices.copy().sort_values("trade_date")
    close = pd.to_numeric(df["close"], errors="coerce")
    volume = pd.to_numeric(df.get("volume", pd.Series([0] * len(df))), errors="coerce").fillna(0)
    amount = pd.to_numeric(df.get("amount", pd.Series([0] * len(df))), errors="coerce").fillna(0)
    ma20 = close.rolling(20).mean()
    high60 = pd.to_numeric(df.get("high", close), errors="coerce").rolling(60).max()

    return {
        "momentum_5d": _period_return(close, 5),
        "momentum_20d": _period_return(close, 20),
        "momentum_60d": _period_return(close, 60),
        "volatility_20d": float(close.pct_change().tail(20).std() or 0.0),
        "volume_ratio_5d": _volume_ratio(volume),
        "ma_distance_20d": _safe_ratio(float(close.iloc[-1]), float(ma20.iloc[-1])),
        "drawdown_from_60d_high": _safe_ratio(float(close.iloc[-1]), float(high60.iloc[-1])),
        "turnover_proxy": float(amount.tail(20).mean() or 0.0),
    }


def future_return(prices: pd.DataFrame, horizon: int) -> float | None:
    if prices.empty or len(prices) <= horizon:
        return None
    df = prices.copy().sort_values("trade_date")
    close = pd.to_numeric(df["close"], errors="coerce")
    if close.iloc[0] <= 0:
        return None
    return float(close.iloc[horizon] / close.iloc[0] - 1)


def _period_return(close: pd.Series, days: int) -> float:
    if len(close) <= days or close.iloc[-days - 1] <= 0:
        return 0.0
    return float(close.iloc[-1] / close.iloc[-days - 1] - 1)


def _volume_ratio(volume: pd.Series) -> float:
    if len(volume) < 20:
        return 0.0
    base = float(volume.tail(20).mean() or 0.0)
    if base <= 0:
        return 0.0
    return float(volume.tail(5).mean() / base - 1)


def _safe_ratio(value: float, base: float) -> float:
    if pd.isna(base) or base <= 0:
        return 0.0
    return float(value / base - 1)
