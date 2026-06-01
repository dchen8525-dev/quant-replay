from __future__ import annotations

import pandas as pd

from src.factors.library import FACTOR_NAMES
from src.factors.metrics import quantile_return_table, rank_ic


def evaluate_factor(data: pd.DataFrame, factor_name: str) -> dict:
    if data.empty or factor_name not in data.columns:
        return {
            "factor": factor_name,
            "rank_ic_5d": 0.0,
            "rank_ic_20d": 0.0,
            "win_rate_top_quantile": 0.0,
            "quantiles": pd.DataFrame(),
        }
    quantiles = quantile_return_table(data, factor_name)
    top_win_rate = 0.0
    if not quantiles.empty:
        top = quantiles.sort_values("quantile").tail(1).iloc[0]
        top_win_rate = float(top["win_rate"])
    return {
        "factor": factor_name,
        "rank_ic_5d": rank_ic(data[factor_name], data["next_5d_return"]),
        "rank_ic_20d": rank_ic(data[factor_name], data["next_20d_return"]),
        "win_rate_top_quantile": top_win_rate,
        "quantiles": quantiles,
    }


def evaluate_all_factors(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for factor in FACTOR_NAMES:
        result = evaluate_factor(data, factor)
        rows.append({key: value for key, value in result.items() if key != "quantiles"})
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("rank_ic_20d", ascending=False)
