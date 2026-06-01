from __future__ import annotations

import pandas as pd


def observed_trade_dates(df: pd.DataFrame) -> list[str]:
    if df.empty or "trade_date" not in df.columns:
        return []
    return sorted(pd.Series(df["trade_date"]).dropna().astype(str).unique().tolist())


def missing_observed_dates(reference: pd.DataFrame, candidate: pd.DataFrame) -> list[str]:
    reference_dates = set(observed_trade_dates(reference))
    candidate_dates = set(observed_trade_dates(candidate))
    return sorted(reference_dates - candidate_dates)
