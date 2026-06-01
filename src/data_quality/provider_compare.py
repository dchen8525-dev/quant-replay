from __future__ import annotations

import pandas as pd

from src.data_quality.calendar import missing_observed_dates


def compare_provider_frames(left: pd.DataFrame, right: pd.DataFrame) -> dict:
    left_clean = _clean(left)
    right_clean = _clean(right)
    merged = left_clean.merge(
        right_clean,
        on="trade_date",
        suffixes=("_left", "_right"),
        how="inner",
    )
    close_diff = pd.Series(dtype=float)
    if not merged.empty and {"close_left", "close_right"}.issubset(merged.columns):
        close_diff = (merged["close_left"] - merged["close_right"]).abs()
    return {
        "left_rows": int(len(left_clean)),
        "right_rows": int(len(right_clean)),
        "left_start": _min_date(left_clean),
        "left_end": _max_date(left_clean),
        "right_start": _min_date(right_clean),
        "right_end": _max_date(right_clean),
        "overlap_rows": int(len(merged)),
        "max_close_diff": float(close_diff.max()) if not close_diff.empty else 0.0,
        "mean_close_diff": float(close_diff.mean()) if not close_diff.empty else 0.0,
        "left_missing_dates": missing_observed_dates(right_clean, left_clean),
        "right_missing_dates": missing_observed_dates(left_clean, right_clean),
    }


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["trade_date", "close"])
    return df.copy().drop_duplicates("trade_date").sort_values("trade_date")


def _min_date(df: pd.DataFrame) -> str | None:
    return None if df.empty else str(df["trade_date"].min())


def _max_date(df: pd.DataFrame) -> str | None:
    return None if df.empty else str(df["trade_date"].max())
