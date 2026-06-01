from __future__ import annotations

import pandas as pd


def validate_price_df(df: pd.DataFrame) -> list[str]:
    warnings: list[str] = []
    if df.empty:
        return ["empty range"]

    required = {"trade_date", "open", "high", "low", "close"}
    missing = required - set(df.columns)
    if missing:
        warnings.append(f"missing columns: {', '.join(sorted(missing))}")
        return warnings

    if df["trade_date"].duplicated().any():
        warnings.append("duplicate dates")

    if df["close"].isna().any():
        warnings.append("missing close")

    price_cols = [col for col in ["open", "high", "low", "close"] if col in df.columns]
    prices = df[price_cols].apply(pd.to_numeric, errors="coerce")
    if (prices <= 0).any().any():
        warnings.append("zero or negative prices")

    dates = pd.to_datetime(df["trade_date"], errors="coerce")
    if dates.isna().any():
        warnings.append("invalid dates")
    elif not dates.is_monotonic_increasing:
        warnings.append("non-monotonic dates")

    return warnings
