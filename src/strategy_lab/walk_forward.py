from __future__ import annotations

import pandas as pd

from src.backtest.engine import run_backtest
from src.strategy_lab.optimizer import _backtest_params
from src.strategy_lab.registry import to_backtest_strategy


def train_test_split(
    prices: pd.DataFrame,
    train_ratio: float = 0.7,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = prices.copy().sort_values("trade_date")
    if len(df) < 4:
        return df, pd.DataFrame(columns=df.columns)
    split = max(1, min(len(df) - 1, int(len(df) * train_ratio)))
    return df.iloc[:split].copy(), df.iloc[split:].copy()


def walk_forward_test(
    prices: pd.DataFrame,
    strategy_name: str,
    params: dict,
    train_ratio: float = 0.7,
    initial_capital: float = 100000.0,
) -> dict:
    train, test = train_test_split(prices, train_ratio)
    if test.empty:
        raise ValueError("test period missing")
    backtest_strategy = to_backtest_strategy(strategy_name)
    clean_params = _backtest_params(strategy_name, params)
    train_result = run_backtest(
        train,
        backtest_strategy,
        clean_params,
        initial_capital=initial_capital,
    )
    test_result = run_backtest(
        test,
        backtest_strategy,
        clean_params,
        initial_capital=initial_capital,
    )
    return {
        "train_metrics": train_result.metrics,
        "test_metrics": test_result.metrics,
        "train_rows": len(train),
        "test_rows": len(test),
    }
