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


def data_health_summary(df: pd.DataFrame) -> dict:
    warnings = validate_price_df(df)
    if df.empty:
        return {
            "rows": 0,
            "start_date": None,
            "end_date": None,
            "duplicate_rows": 0,
            "missing_close": 0,
            "warnings": warnings,
        }
    return {
        "rows": int(len(df)),
        "start_date": str(df["trade_date"].min()) if "trade_date" in df else None,
        "end_date": str(df["trade_date"].max()) if "trade_date" in df else None,
        "duplicate_rows": int(df["trade_date"].duplicated().sum()) if "trade_date" in df else 0,
        "missing_close": int(df["close"].isna().sum()) if "close" in df else 0,
        "warnings": warnings,
    }
