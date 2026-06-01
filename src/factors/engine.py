from __future__ import annotations

import pandas as pd

from src.factors.library import calculate_factors, future_return


def build_factor_table(price_map: dict[str, pd.DataFrame], metadata: pd.DataFrame) -> pd.DataFrame:
    rows = []
    meta = metadata.set_index("code").to_dict("index") if not metadata.empty else {}
    for code, prices in price_map.items():
        factors = calculate_factors(prices)
        row = {
            "code": code,
            "name": meta.get(code, {}).get("name", ""),
            "category": meta.get(code, {}).get("category", ""),
            **factors,
            "next_5d_return": future_return(prices.tail(6), 5),
            "next_20d_return": future_return(prices.tail(21), 20),
        }
        rows.append(row)
    return pd.DataFrame(rows)


def rank_factor_table(data: pd.DataFrame, factor_name: str) -> pd.DataFrame:
    if data.empty or factor_name not in data.columns:
        return data
    ranked = data.copy()
    ranked["factor_rank"] = ranked[factor_name].rank(ascending=False, method="min")
    return ranked.sort_values("factor_rank")
