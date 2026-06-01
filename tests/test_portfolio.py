from __future__ import annotations

import pandas as pd
import pytest

from src.portfolio.construction import (
    construct_portfolio,
    equal_weight,
    risk_adjusted_weight,
    score_weighted,
)
from src.portfolio.metrics import portfolio_metrics
from src.portfolio.rebalance import rebalance_dates, run_portfolio_backtest
from src.portfolio.risk import category_exposure, single_stock_exposure, validate_limits


def universe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"code": "A", "name": "A", "category": "新能源", "score": 90, "volatility": 0.1},
            {"code": "B", "name": "B", "category": "新能源", "score": 30, "volatility": 0.2},
            {"code": "C", "name": "C", "category": "消费", "score": 60, "volatility": 0.05},
        ]
    )


def prices(base: float, days: int = 45) -> pd.DataFrame:
    closes = [base + i for i in range(days)]
    return pd.DataFrame(
        {
            "trade_date": [f"2026-05-{(i % 28) + 1:02d}" for i in range(days)],
            "open": closes,
            "high": [value + 1 for value in closes],
            "low": [value - 1 for value in closes],
            "close": closes,
            "volume": [100] * days,
        }
    )


def test_equal_weight_and_limits() -> None:
    weights = equal_weight(universe(), max_position=0.2, cash_reserve=0.1)
    assert weights["target_weight"].max() <= 0.2
    assert weights["target_weight"].sum() <= 0.9


def test_score_weighted_orders_by_score() -> None:
    weights = score_weighted(universe(), max_position=0.8, cash_reserve=0)
    assert weights.iloc[0]["code"] == "A"


def test_risk_adjusted_weight_prefers_low_risk() -> None:
    weights = risk_adjusted_weight(universe(), max_position=0.8, cash_reserve=0)
    assert weights.iloc[0]["code"] in {"A", "C"}


def test_exposure_tables_and_validation() -> None:
    weights = construct_portfolio(
        universe(), method="equal", max_position=0.5, max_category_exposure=0.4
    )
    assert not category_exposure(weights).empty
    assert not single_stock_exposure(weights).empty
    assert validate_limits(weights, max_position=0.5, max_category_exposure=0.4) == []


def test_portfolio_metrics() -> None:
    curve = pd.DataFrame({"trade_date": ["1", "2", "3"], "equity": [100, 110, 105]})
    metrics = portfolio_metrics(curve, turnover=0.2)
    assert metrics["portfolio_return"] == pytest.approx(0.05)
    assert metrics["max_drawdown"] < 0
    assert metrics["turnover"] == 0.2


def test_rebalance_and_portfolio_backtest() -> None:
    price_map = {"A": prices(10), "B": prices(20), "C": prices(30)}
    assert len(rebalance_dates(price_map, "weekly")) > len(rebalance_dates(price_map, "monthly"))
    result = run_portfolio_backtest(
        price_map,
        universe(),
        method="score",
        initial_capital=100000,
        benchmark_prices=prices(100),
    )
    assert result["metrics"]["portfolio_return"] > 0
    assert "benchmark_return" in result["metrics"]
    assert not result["weights"].empty
