from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class BacktestTrade:
    entry_date: str
    entry_price: float
    exit_date: str | None
    exit_price: float | None
    quantity: int
    profit: float
    return_rate: float
    holding_days: int
    exit_reason: str


@dataclass(frozen=True)
class BacktestResult:
    metrics: dict
    equity_curve: pd.DataFrame
    trades: pd.DataFrame
    signals: pd.DataFrame
    benchmark_curve: pd.DataFrame
