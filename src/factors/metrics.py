from __future__ import annotations

import pandas as pd


def rank_ic(values: pd.Series, returns: pd.Series) -> float:
    df = pd.DataFrame({"factor": values, "return": returns}).dropna()
    if len(df) < 2:
        return 0.0
    if df["factor"].nunique() < 2 or df["return"].nunique() < 2:
        return 0.0
    corr = df["factor"].rank().corr(df["return"].rank())
    return 0.0 if pd.isna(corr) else float(corr)


def quantile_return_table(
    data: pd.DataFrame,
    factor_name: str,
    return_col: str = "next_20d_return",
    quantiles: int = 5,
) -> pd.DataFrame:
    if data.empty or factor_name not in data or return_col not in data:
        return pd.DataFrame(columns=["quantile", "count", "win_rate", "average_return"])
    df = data[["code", factor_name, return_col]].dropna().copy()
    if df.empty:
        return pd.DataFrame(columns=["quantile", "count", "win_rate", "average_return"])
    bins = min(quantiles, df[factor_name].nunique(), len(df))
    if bins <= 1:
        df["quantile"] = "Q1"
    else:
        df["quantile"] = pd.qcut(df[factor_name].rank(method="first"), bins, labels=False) + 1
        df["quantile"] = "Q" + df["quantile"].astype(str)
    return (
        df.groupby("quantile")
        .agg(
            count=("code", "count"),
            win_rate=(return_col, lambda s: float((s > 0).mean())),
            average_return=(return_col, "mean"),
        )
        .reset_index()
    )
