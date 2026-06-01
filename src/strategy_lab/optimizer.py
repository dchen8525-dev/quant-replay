from __future__ import annotations

from itertools import product

import pandas as pd

from src.backtest.engine import run_backtest
from src.strategy_lab.registry import to_backtest_strategy


def parameter_grid(grid: dict[str, list]) -> list[dict]:
    if not grid:
        return [{}]
    keys = list(grid)
    return [
        dict(zip(keys, values, strict=False))
        for values in product(*[grid[key] for key in keys])
    ]


def run_parameter_grid(
    prices: pd.DataFrame,
    strategy_name: str,
    grid: dict[str, list],
    initial_capital: float = 100000.0,
) -> pd.DataFrame:
    rows = []
    for params in parameter_grid(grid):
        result = run_backtest(
            prices,
            to_backtest_strategy(strategy_name),
            _backtest_params(strategy_name, params),
            initial_capital=initial_capital,
        )
        rows.append(
            {
                "strategy_name": strategy_name,
                "params": params,
                **result.metrics,
            }
        )
    return pd.DataFrame(rows).sort_values("total_return", ascending=False)


def _backtest_params(strategy_name: str, params: dict) -> dict:
    if strategy_name == "MA Cross":
        return params
    if strategy_name == "Breakout":
        return params
    if strategy_name == "Mean Reversion":
        return params
    if strategy_name == "Strength Rotation":
        return {"ma_short": 5, "ma_long": 20}
    if strategy_name == "Factor Ranking":
        return {"window": 20, "ma_exit": 10}
    return params
