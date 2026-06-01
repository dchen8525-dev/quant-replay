from __future__ import annotations

import pandas as pd

from src import database
from src.strategy_lab.experiment import (
    anti_overfitting_warnings,
    experiment_history,
    save_experiment,
    save_experiment_result,
)
from src.strategy_lab.optimizer import parameter_grid, run_parameter_grid
from src.strategy_lab.registry import get_strategy, list_strategies
from src.strategy_lab.walk_forward import train_test_split, walk_forward_test


def prices(days: int = 80) -> pd.DataFrame:
    closes = [10 + i * 0.2 for i in range(days)]
    return pd.DataFrame(
        {
            "trade_date": [f"2026-05-{(i % 28) + 1:02d}" for i in range(days)],
            "open": closes,
            "high": [value + 0.5 for value in closes],
            "low": [value - 0.5 for value in closes],
            "close": closes,
            "volume": [100] * days,
        }
    )


def test_strategy_registry() -> None:
    names = list_strategies()
    assert "MA Cross" in names
    assert "Factor Ranking" in names
    assert get_strategy("Breakout").params


def test_parameter_grid() -> None:
    grid = parameter_grid({"a": [1, 2], "b": [3, 4]})
    assert len(grid) == 4
    assert {"a": 1, "b": 3} in grid


def test_run_parameter_grid() -> None:
    result = run_parameter_grid(
        prices(),
        "MA Cross",
        {"ma_short": [2, 3], "ma_long": [5]},
        initial_capital=100000,
    )
    assert len(result) == 2
    assert "total_return" in result.columns


def test_walk_forward_split_and_test() -> None:
    train, test = train_test_split(prices(), 0.7)
    assert len(train) > len(test)
    result = walk_forward_test(
        prices(),
        "MA Cross",
        {"ma_short": 2, "ma_long": 5},
        train_ratio=0.7,
    )
    assert result["train_rows"] > 0
    assert result["test_rows"] > 0
    assert "total_return" in result["test_metrics"]


def test_experiment_persistence(tmp_path) -> None:
    database.set_db_path(tmp_path / "test.db")
    database.init_db()
    exp_id = save_experiment(
        "test",
        "MA Cross",
        {"ma_short": 2, "ma_long": 5},
        ["002594"],
        "2026-05-01",
        "2026-06-01",
        "沪深300",
    )
    save_experiment_result(exp_id, {"total_return": 0.1, "max_drawdown": -0.05, "trade_count": 2})
    history = experiment_history()
    assert len(history) == 1
    assert history.iloc[0]["strategy_name"] == "MA Cross"
    database.reset_db_path()


def test_anti_overfitting_warnings() -> None:
    warnings = anti_overfitting_warnings(
        {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
        {"total_return": 2.0, "trade_count": 1},
        train_rows=10,
        test_rows=0,
    )
    assert "too many parameters" in warnings
    assert "too few trades" in warnings
    assert "test period missing" in warnings
