from __future__ import annotations

import pandas as pd

from src.regime.metrics import period_return, prepare_prices


def category_rotation(
    price_frames: dict[str, pd.DataFrame],
    watchlist: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict] = []
    if watchlist.empty:
        return pd.DataFrame()
    meta = watchlist.set_index("code").to_dict("index")
    for code, prices in price_frames.items():
        df = prepare_prices(prices)
        if df.empty or code not in meta:
            continue
        close = df["close"]
        rows.append(
            {
                "code": code,
                "name": meta[code].get("name", ""),
                "category": meta[code].get("category", "其他"),
                "5d_return": period_return(close, 5),
                "20d_return": period_return(close, 20),
                "60d_return": period_return(close, 60),
                "above_ma20": bool(
                    close.iloc[-1] > close.rolling(20, min_periods=1).mean().iloc[-1]
                ),
            }
        )
    return category_rotation_from_rows(pd.DataFrame(rows))


def category_rotation_from_rows(rows: pd.DataFrame) -> pd.DataFrame:
    if rows.empty or "category" not in rows.columns:
        return pd.DataFrame()
    df = (
        rows.groupby("category")
        .agg(
            average_5d_return=("5d_return", "mean"),
            average_20d_return=("20d_return", "mean"),
            average_60d_return=("60d_return", "mean"),
            above_ma20_ratio=("above_ma20", "mean"),
            stock_count=("code", "count"),
            strongest_stock=("code", "first"),
        )
        .reset_index()
    )
    rank_cols = [
        "average_5d_return",
        "average_20d_return",
        "average_60d_return",
        "above_ma20_ratio",
    ]
    for col in rank_cols:
        df[f"{col}_rank"] = df[col].rank(pct=True)
    df["strength_score"] = (
        35 * df["average_20d_return_rank"]
        + 25 * df["average_60d_return_rank"]
        + 20 * df["average_5d_return_rank"]
        + 20 * df["above_ma20_ratio_rank"]
    )
    df["rotation_state"] = df.apply(_rotation_state, axis=1)
    return df.sort_values("strength_score", ascending=False).reset_index(drop=True)


def rotation_buckets(rotation: pd.DataFrame) -> dict[str, list[str]]:
    if rotation.empty:
        return {"strong": [], "weakening": [], "improving": []}
    return {
        "strong": rotation.loc[rotation["rotation_state"] == "strong", "category"].tolist(),
        "weakening": rotation.loc[rotation["rotation_state"] == "weakening", "category"].tolist(),
        "improving": rotation.loc[rotation["rotation_state"] == "improving", "category"].tolist(),
    }


def _rotation_state(row: pd.Series) -> str:
    if row["average_5d_return"] < 0 and row["average_20d_return"] > 0:
        return "weakening"
    if row["average_5d_return"] > 0 and row["average_20d_return"] <= 0:
        return "improving"
    if (
        row["average_20d_return"] > 0
        and row["average_60d_return"] > 0
        and row["above_ma20_ratio"] >= 0.5
    ):
        return "strong"
    return "neutral"
