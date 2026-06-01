from __future__ import annotations

import pandas as pd


def equal_weight(
    universe: pd.DataFrame,
    max_position: float = 0.2,
    cash_reserve: float = 0.1,
) -> pd.DataFrame:
    selected = universe.copy()
    if selected.empty:
        return _empty_weights()
    investable = max(0.0, 1 - cash_reserve)
    raw_weight = investable / len(selected)
    selected["target_weight"] = min(raw_weight, max_position)
    return _normalize(selected, investable)


def score_weighted(
    universe: pd.DataFrame,
    score_col: str = "score",
    max_position: float = 0.2,
    cash_reserve: float = 0.1,
) -> pd.DataFrame:
    selected = universe.copy()
    if selected.empty:
        return _empty_weights()
    investable = max(0.0, 1 - cash_reserve)
    score = pd.to_numeric(selected.get(score_col, 1), errors="coerce").clip(lower=0).fillna(0)
    if score.sum() <= 0:
        return equal_weight(selected, max_position, cash_reserve)
    selected["target_weight"] = score / score.sum() * investable
    selected["target_weight"] = selected["target_weight"].clip(upper=max_position)
    return _normalize(selected, investable)


def risk_adjusted_weight(
    universe: pd.DataFrame,
    score_col: str = "score",
    volatility_col: str = "volatility",
    max_position: float = 0.2,
    cash_reserve: float = 0.1,
) -> pd.DataFrame:
    selected = universe.copy()
    if selected.empty:
        return _empty_weights()
    investable = max(0.0, 1 - cash_reserve)
    score = pd.to_numeric(selected.get(score_col, 1), errors="coerce").clip(lower=0).fillna(0)
    vol = pd.to_numeric(selected.get(volatility_col, 1), errors="coerce").fillna(1).clip(lower=1e-6)
    risk_score = score / vol
    if risk_score.sum() <= 0:
        return equal_weight(selected, max_position, cash_reserve)
    selected["target_weight"] = risk_score / risk_score.sum() * investable
    selected["target_weight"] = selected["target_weight"].clip(upper=max_position)
    return _normalize(selected, investable)


def apply_category_limit(
    weights: pd.DataFrame,
    max_category_exposure: float = 0.4,
) -> pd.DataFrame:
    if weights.empty or "category" not in weights.columns:
        return weights
    adjusted = weights.copy()
    for category, group in adjusted.groupby("category"):
        exposure = group["target_weight"].sum()
        if exposure > max_category_exposure:
            scale = max_category_exposure / exposure
            adjusted.loc[group.index, "target_weight"] *= scale
    return adjusted


def construct_portfolio(
    universe: pd.DataFrame,
    method: str = "equal",
    score_col: str = "score",
    max_position: float = 0.2,
    max_category_exposure: float = 0.4,
    cash_reserve: float = 0.1,
) -> pd.DataFrame:
    if method == "score":
        weights = score_weighted(universe, score_col, max_position, cash_reserve)
    elif method == "risk_adjusted":
        weights = risk_adjusted_weight(
            universe, score_col, "volatility", max_position, cash_reserve
        )
    else:
        weights = equal_weight(universe, max_position, cash_reserve)
    return apply_category_limit(weights, max_category_exposure)


def _normalize(weights: pd.DataFrame, investable: float) -> pd.DataFrame:
    result = weights.copy()
    total = result["target_weight"].sum()
    if total > investable and total > 0:
        result["target_weight"] = result["target_weight"] / total * investable
    return result.sort_values("target_weight", ascending=False)


def _empty_weights() -> pd.DataFrame:
    return pd.DataFrame(columns=["code", "name", "category", "target_weight"])
