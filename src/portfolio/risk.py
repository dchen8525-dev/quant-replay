from __future__ import annotations

import pandas as pd


def category_exposure(weights: pd.DataFrame) -> pd.DataFrame:
    if weights.empty or "category" not in weights.columns:
        return pd.DataFrame(columns=["category", "exposure"])
    return (
        weights.groupby("category")["target_weight"]
        .sum()
        .reset_index(name="exposure")
        .sort_values("exposure", ascending=False)
    )


def single_stock_exposure(weights: pd.DataFrame) -> pd.DataFrame:
    if weights.empty:
        return pd.DataFrame(columns=["code", "name", "target_weight"])
    columns = [col for col in ["code", "name", "target_weight"] if col in weights.columns]
    return weights[columns].sort_values("target_weight", ascending=False)


def validate_limits(
    weights: pd.DataFrame,
    max_position: float = 0.2,
    max_category_exposure: float = 0.4,
) -> list[str]:
    warnings: list[str] = []
    if weights.empty:
        return warnings
    if weights["target_weight"].max() > max_position + 1e-9:
        warnings.append("single stock exposure exceeds limit")
    category = category_exposure(weights)
    if not category.empty and category["exposure"].max() > max_category_exposure + 1e-9:
        warnings.append("category exposure exceeds limit")
    return warnings
