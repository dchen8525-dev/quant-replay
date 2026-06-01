from __future__ import annotations

import pandas as pd


def moving_average_cross(
    prices: pd.DataFrame, ma_short: int = 5, ma_long: int = 20
) -> pd.DataFrame:
    df = prices.copy().sort_values("trade_date")
    short = df["close"].rolling(ma_short).mean()
    long = df["close"].rolling(ma_long).mean()
    previous_short = short.shift(1)
    previous_long = long.shift(1)
    buy = (short > long) & (previous_short <= previous_long)
    sell = (short < long) & (previous_short >= previous_long)
    return _signals(df, buy, sell)


def breakout(prices: pd.DataFrame, window: int = 20, ma_exit: int = 10) -> pd.DataFrame:
    df = prices.copy().sort_values("trade_date")
    previous_high = df["high"].rolling(window).max().shift(1)
    exit_ma = df["close"].rolling(ma_exit).mean()
    buy = df["close"] > previous_high
    sell = df["close"] < exit_ma
    return _signals(df, buy, sell)


def mean_reversion(prices: pd.DataFrame, ma: int = 20, threshold: float = -0.05) -> pd.DataFrame:
    df = prices.copy().sort_values("trade_date")
    average = df["close"].rolling(ma).mean()
    distance = df["close"] / average - 1
    buy = distance < threshold
    sell = df["close"] >= average
    return _signals(df, buy, sell)


def build_signals(strategy_name: str, prices: pd.DataFrame, params: dict) -> pd.DataFrame:
    if strategy_name == "Moving Average Cross":
        return moving_average_cross(
            prices,
            int(params.get("ma_short", 5)),
            int(params.get("ma_long", 20)),
        )
    if strategy_name == "Breakout":
        return breakout(
            prices,
            int(params.get("window", 20)),
            int(params.get("ma_exit", 10)),
        )
    if strategy_name == "Mean Reversion":
        return mean_reversion(
            prices,
            int(params.get("ma", 20)),
            float(params.get("threshold", -0.05)),
        )
    raise ValueError(f"Unknown strategy: {strategy_name}")


def _signals(df: pd.DataFrame, buy: pd.Series, sell: pd.Series) -> pd.DataFrame:
    signals = df[["trade_date", "open", "high", "low", "close"]].copy()
    signals["signal"] = 0
    signals.loc[buy.fillna(False), "signal"] = 1
    signals.loc[sell.fillna(False), "signal"] = -1
    return signals
