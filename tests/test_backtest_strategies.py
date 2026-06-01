from __future__ import annotations

import pandas as pd

from src.backtest.strategies import breakout, mean_reversion, moving_average_cross


def strategy_prices() -> pd.DataFrame:
    closes = [10, 10, 10, 10, 10, 11, 12, 13, 12, 11, 10, 9]
    return pd.DataFrame(
        {
            "trade_date": [f"2026-05-{i:02d}" for i in range(1, len(closes) + 1)],
            "open": closes,
            "high": [value + 0.5 for value in closes],
            "low": [value - 0.5 for value in closes],
            "close": closes,
            "volume": [100] * len(closes),
        }
    )


def test_ma_cross_generates_expected_trade_signals() -> None:
    signals = moving_average_cross(strategy_prices(), ma_short=2, ma_long=4)
    assert 1 in signals["signal"].values
    assert -1 in signals["signal"].values


def test_breakout_generates_buy_signal() -> None:
    signals = breakout(strategy_prices(), window=3, ma_exit=3)
    assert 1 in signals["signal"].values


def test_mean_reversion_generates_buy_signal() -> None:
    signals = mean_reversion(strategy_prices(), ma=3, threshold=-0.05)
    assert 1 in signals["signal"].values
