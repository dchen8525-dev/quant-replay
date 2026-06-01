from __future__ import annotations

import pandas as pd


def stock_strength(prices: pd.DataFrame, meta: dict | None = None) -> dict:
    meta = meta or {}
    if prices.empty or len(prices) < 2:
        return {
            **meta,
            "5d_return": 0.0,
            "10d_return": 0.0,
            "20d_return": 0.0,
            "60d_return": 0.0,
            "volatility": 0.0,
            "distance_to_20d_high": 0.0,
            "distance_to_high": 0.0,
            "trend": "insufficient",
            "volume_change": 0.0,
            "score": 0.0,
        }
    df = prices.copy().sort_values("trade_date")
    close = df["close"]
    high = df["high"]
    ma5 = close.rolling(5).mean()
    ma20 = close.rolling(20).mean()
    volume = df["volume"] if "volume" in df.columns else pd.Series([0] * len(df))
    row = {
        **meta,
        "5d_return": _period_return(close, 5),
        "10d_return": _period_return(close, 10),
        "20d_return": _period_return(close, 20),
        "60d_return": _period_return(close, 60),
        "volatility": float(close.pct_change().tail(20).std() or 0),
        "distance_to_20d_high": float(close.iloc[-1] / high.tail(20).max() - 1),
        "distance_to_high": float(close.iloc[-1] / high.tail(60).max() - 1),
        "trend": "rising" if ma5.iloc[-1] > ma20.iloc[-1] else "falling",
        "volume_change": float(volume.tail(5).mean() / volume.tail(20).mean() - 1)
        if volume.tail(20).mean()
        else 0.0,
    }
    return row


def rank_strength(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    numeric_cols = ["20d_return", "60d_return", "distance_to_high", "volatility"]
    df[numeric_cols] = df[numeric_cols].fillna(0.0)
    for col in ["20d_return", "60d_return", "distance_to_high"]:
        df[f"{col}_rank"] = df[col].rank(pct=True)
    df["inverse_volatility_rank"] = (-df["volatility"]).rank(pct=True)
    df["MA_trend_score"] = (df["trend"] == "rising").astype(float)
    df["score"] = (
        30 * df["20d_return_rank"]
        + 20 * df["60d_return_rank"]
        + 20 * df["distance_to_high_rank"]
        + 15 * df["MA_trend_score"]
        + 15 * df["inverse_volatility_rank"]
    )
    df = df.sort_values("score", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    return df


def category_strength(strength_df: pd.DataFrame) -> pd.DataFrame:
    if strength_df.empty or "category" not in strength_df.columns:
        return pd.DataFrame()
    return (
        strength_df.groupby("category")
        .agg(
            average_5d_return=("5d_return", "mean"),
            average_20d_return=("20d_return", "mean"),
            average_60d_return=("60d_return", "mean"),
            rising_stocks=("trend", lambda s: int((s == "rising").sum())),
            percentage_above_ma20=("trend", lambda s: float((s == "rising").mean())),
            best_stock=("code", "first"),
            worst_stock=("code", "last"),
        )
        .reset_index()
        .sort_values("average_20d_return", ascending=False)
    )


def _period_return(close: pd.Series, days: int) -> float:
    if len(close) <= days:
        return 0.0
    return float(close.iloc[-1] / close.iloc[-days - 1] - 1)
