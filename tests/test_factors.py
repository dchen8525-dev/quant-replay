from __future__ import annotations

import pandas as pd

from src.factors.engine import build_factor_table, rank_factor_table
from src.factors.evaluator import evaluate_all_factors, evaluate_factor
from src.factors.library import calculate_factors
from src.factors.metrics import quantile_return_table, rank_ic


def prices(base: float = 10.0, slope: float = 1.0) -> pd.DataFrame:
    closes = [base + i * slope for i in range(90)]
    return pd.DataFrame(
        {
            "trade_date": [f"2026-01-{(i % 28) + 1:02d}" for i in range(90)],
            "open": closes,
            "high": [value + 0.5 for value in closes],
            "low": [value - 0.5 for value in closes],
            "close": closes,
            "volume": [100 + i for i in range(90)],
            "amount": [(100 + i) * closes[i] for i in range(90)],
        }
    )


def test_factor_calculations() -> None:
    factors = calculate_factors(prices())
    assert factors["momentum_5d"] > 0
    assert factors["momentum_20d"] > 0
    assert factors["momentum_60d"] > 0
    assert "volatility_20d" in factors
    assert factors["turnover_proxy"] > 0


def test_missing_data_returns_zero_factors() -> None:
    factors = calculate_factors(pd.DataFrame())
    assert all(value == 0 for value in factors.values())


def test_factor_table_and_ranking() -> None:
    metadata = pd.DataFrame(
        [
            {"code": "A", "name": "A", "category": "新能源"},
            {"code": "B", "name": "B", "category": "消费"},
        ]
    )
    table = build_factor_table({"A": prices(10, 1), "B": prices(10, 0.1)}, metadata)
    ranked = rank_factor_table(table, "momentum_20d")
    assert ranked.iloc[0]["factor_rank"] == 1
    assert set(table["code"]) == {"A", "B"}


def test_quantile_grouping_and_ic() -> None:
    data = pd.DataFrame(
        {
            "code": ["A", "B", "C", "D"],
            "factor": [1, 2, 3, 4],
            "next_20d_return": [0.01, 0.02, 0.03, 0.04],
        }
    )
    assert rank_ic(data["factor"], data["next_20d_return"]) == 1.0
    quantiles = quantile_return_table(data, "factor", quantiles=2)
    assert len(quantiles) == 2
    assert quantiles["average_return"].iloc[-1] > quantiles["average_return"].iloc[0]


def test_factor_evaluation() -> None:
    data = pd.DataFrame(
        {
            "code": ["A", "B", "C"],
            "momentum_5d": [1, 2, 3],
            "momentum_20d": [1, 2, 3],
            "momentum_60d": [1, 2, 3],
            "volatility_20d": [3, 2, 1],
            "volume_ratio_5d": [1, 1, 1],
            "ma_distance_20d": [1, 2, 3],
            "drawdown_from_60d_high": [-0.2, -0.1, 0],
            "turnover_proxy": [10, 20, 30],
            "next_5d_return": [0.01, 0.02, 0.03],
            "next_20d_return": [0.01, 0.02, 0.03],
        }
    )
    result = evaluate_factor(data, "momentum_20d")
    summary = evaluate_all_factors(data)
    assert result["rank_ic_20d"] == 1.0
    assert not summary.empty
