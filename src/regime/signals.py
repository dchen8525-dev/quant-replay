from __future__ import annotations


def trend_label(close: float, ma20: float, ma60: float, drawdown_60d: float) -> str:
    if close > ma20 > ma60 and drawdown_60d > -0.08:
        return "bull trend"
    if close < ma20 < ma60 or drawdown_60d <= -0.15:
        return "bear trend"
    return "sideways"


def volatility_label(percentile: float) -> str:
    if percentile >= 0.7:
        return "high volatility"
    if percentile <= 0.3:
        return "low volatility"
    return "normal volatility"


def risk_label(trend: str, volatility: str, drawdown_60d: float) -> str:
    if trend == "bull trend" and volatility != "high volatility":
        return "risk-on"
    if trend == "bear trend" or drawdown_60d <= -0.12:
        return "risk-off"
    return "neutral"
