from __future__ import annotations

import pandas as pd
import pytest

from src.analyzer import analyze_trade, compare_with_benchmark


def fake_prices() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"trade_date": "2026-05-04", "open": 10, "high": 11, "low": 9.6, "close": 10},
            {"trade_date": "2026-05-05", "open": 10, "high": 12, "low": 9.4, "close": 11},
            {"trade_date": "2026-05-06", "open": 11, "high": 13, "low": 10.5, "close": 12},
            {"trade_date": "2026-05-07", "open": 12, "high": 12, "low": 9.0, "close": 9},
        ]
    )


def test_analyze_trade_metrics() -> None:
    result = analyze_trade(fake_prices(), 10, 100, "2026-05-04")
    assert result["final_return"] == pytest.approx(-0.1)
    assert result["final_profit"] == pytest.approx(-100)
    assert result["max_floating_profit"] == pytest.approx(0.3)
    assert result["max_floating_loss"] == pytest.approx(-0.1)
    assert result["max_drawdown"] == pytest.approx(-0.25)
    assert result["holding_days"] == 4


def test_stop_loss_simulation() -> None:
    result = analyze_trade(fake_prices(), 10, 100, "2026-05-04")
    stops = {row["threshold"]: row for row in result["stop_loss"]}
    assert stops[-0.03]["triggered"]
    assert stops[-0.05]["triggered"]
    assert stops[-0.08]["triggered"]
    assert stops[-0.1]["triggered"]


def test_non_trading_buy_date_uses_next_trading_day() -> None:
    result = analyze_trade(fake_prices(), 10, 100, "2026-05-03")
    assert result["actual_start_date"] == "2026-05-04"


def test_invalid_inputs() -> None:
    with pytest.raises(ValueError):
        analyze_trade(pd.DataFrame(), 10, 100, "2026-05-04")
    with pytest.raises(ValueError):
        analyze_trade(fake_prices(), 0, 100, "2026-05-04")
    with pytest.raises(ValueError):
        analyze_trade(fake_prices(), 10, 0, "2026-05-04")


def test_benchmark_comparison() -> None:
    stock = analyze_trade(fake_prices(), 10, 100, "2026-05-04")["series"]
    benchmark = fake_prices().assign(close=[100, 101, 102, 103])
    result = compare_with_benchmark(stock, benchmark)
    assert result["stock_return"] == pytest.approx(-0.1)
    assert result["benchmark_return"] == pytest.approx(0.03)
    assert result["excess_return"] == pytest.approx(-0.13)
    assert not result["outperformed"]
