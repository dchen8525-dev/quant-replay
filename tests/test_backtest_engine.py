from __future__ import annotations

import pandas as pd
import pytest

from src.backtest.engine import run_backtest
from src.backtest.metrics import max_drawdown


def prices() -> pd.DataFrame:
    closes = [10, 10, 10, 10, 10, 11, 12, 13, 12, 11, 10, 9]
    return pd.DataFrame(
        {
            "trade_date": [f"2026-05-{i:02d}" for i in range(1, len(closes) + 1)],
            "open": [value + 0.1 for value in closes],
            "high": [value + 0.5 for value in closes],
            "low": [value - 0.5 for value in closes],
            "close": closes,
            "volume": [100] * len(closes),
        }
    )


def test_no_lookahead_execution_uses_next_open() -> None:
    result = run_backtest(
        prices(),
        "Moving Average Cross",
        {"ma_short": 2, "ma_long": 4},
        commission_rate=0,
        slippage_rate=0,
    )
    first_buy_signal_index = result.signals.index[result.signals["signal"] == 1][0]
    expected_entry = prices().iloc[first_buy_signal_index + 1]
    assert result.trades.iloc[0]["entry_date"] == expected_entry["trade_date"]
    assert result.trades.iloc[0]["entry_price"] == expected_entry["open"]


def test_commission_reduces_final_equity() -> None:
    no_fee = run_backtest(
        prices(), "Moving Average Cross", {"ma_short": 2, "ma_long": 4}, 100000, 0, 0
    )
    fee = run_backtest(
        prices(), "Moving Average Cross", {"ma_short": 2, "ma_long": 4}, 100000, 0.01, 0
    )
    assert fee.metrics["final_equity"] < no_fee.metrics["final_equity"]


def test_slippage_affects_execution_price() -> None:
    result = run_backtest(
        prices(),
        "Moving Average Cross",
        {"ma_short": 2, "ma_long": 4},
        commission_rate=0,
        slippage_rate=0.01,
    )
    assert result.trades.iloc[0]["entry_price"] > 0
    assert result.trades.iloc[0]["entry_price"] != prices().iloc[6]["open"]


def test_max_drawdown_calculation() -> None:
    assert max_drawdown(pd.Series([100, 120, 90])) == pytest.approx(-0.25)


def test_empty_and_single_row_price_data() -> None:
    with pytest.raises(ValueError):
        run_backtest(pd.DataFrame(), "Moving Average Cross")
    with pytest.raises(ValueError):
        run_backtest(prices().head(1), "Moving Average Cross")
