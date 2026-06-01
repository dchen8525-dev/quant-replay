from __future__ import annotations

import math

import pandas as pd


def max_drawdown(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    running_max = equity.cummax()
    drawdown = equity / running_max - 1
    return float(drawdown.min())


def annualized_return(total_return: float, trading_days: int) -> float:
    if trading_days <= 0:
        return 0.0
    return float((1 + total_return) ** (252 / trading_days) - 1)


def trade_metrics(trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {
            "win_rate": 0.0,
            "trade_count": 0,
            "average_profit": 0.0,
            "average_loss": 0.0,
            "profit_factor": 0.0,
            "holding_days": 0.0,
        }

    profits = pd.to_numeric(trades["profit"], errors="coerce").fillna(0)
    wins = profits[profits > 0]
    losses = profits[profits < 0]
    gross_profit = float(wins.sum())
    gross_loss = abs(float(losses.sum()))
    profit_factor = math.inf if gross_loss == 0 and gross_profit > 0 else 0.0
    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss

    return {
        "win_rate": float((profits > 0).mean()),
        "trade_count": int(len(trades)),
        "average_profit": float(wins.mean()) if not wins.empty else 0.0,
        "average_loss": float(losses.mean()) if not losses.empty else 0.0,
        "profit_factor": float(profit_factor),
        "holding_days": float(trades["holding_days"].mean()),
    }
