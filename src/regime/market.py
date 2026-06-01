from __future__ import annotations

import pandas as pd

from src.regime.metrics import drawdown_from_high, prepare_prices, volatility_percentile
from src.regime.signals import risk_label, trend_label, volatility_label


def market_regime_summary(prices: pd.DataFrame) -> dict:
    df = prepare_prices(prices)
    if df.empty:
        return {
            "trend": "insufficient",
            "volatility": "insufficient",
            "risk": "insufficient",
            "labels": ["insufficient"],
            "close": 0.0,
            "ma20": 0.0,
            "ma60": 0.0,
            "drawdown_60d": 0.0,
            "volatility_percentile": 0.0,
        }

    close = df["close"]
    ma20 = float(close.rolling(20, min_periods=1).mean().iloc[-1])
    ma60 = float(close.rolling(60, min_periods=1).mean().iloc[-1])
    latest = float(close.iloc[-1])
    drawdown = drawdown_from_high(close, 60)
    vol_pct = volatility_percentile(close, 20)

    trend = trend_label(latest, ma20, ma60, drawdown)
    volatility = volatility_label(vol_pct)
    risk = risk_label(trend, volatility, drawdown)
    labels = [trend]
    if volatility != "normal volatility":
        labels.append(volatility)
    if risk != "neutral":
        labels.append(risk)

    return {
        "trend": trend,
        "volatility": volatility,
        "risk": risk,
        "labels": labels,
        "close": latest,
        "ma20": ma20,
        "ma60": ma60,
        "drawdown_60d": drawdown,
        "volatility_percentile": vol_pct,
    }


def regime_series(prices: pd.DataFrame) -> pd.DataFrame:
    df = prepare_prices(prices)
    if df.empty:
        return pd.DataFrame()
    close = df["close"]
    result = df[["trade_date", "close"]].copy()
    result["ma20"] = close.rolling(20, min_periods=1).mean()
    result["ma60"] = close.rolling(60, min_periods=1).mean()
    result["drawdown_60d"] = close / close.rolling(60, min_periods=1).max() - 1
    result["volatility_20d"] = close.pct_change().rolling(20).std().fillna(0.0)
    return result
