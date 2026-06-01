from __future__ import annotations

import pandas as pd

from src.strength import category_strength, rank_strength, stock_strength


def prices(base: float) -> pd.DataFrame:
    closes = [base + i for i in range(70)]
    return pd.DataFrame(
        {
            "trade_date": [f"2026-03-{(i % 28) + 1:02d}" for i in range(70)],
            "open": closes,
            "high": [value + 1 for value in closes],
            "low": [value - 1 for value in closes],
            "close": closes,
            "volume": [100 + i for i in range(70)],
        }
    )


def test_return_calculations() -> None:
    row = stock_strength(prices(10), {"code": "A", "category": "新能源"})
    assert row["20d_return"] > 0
    assert row["trend"] == "rising"


def test_ranking_order_and_missing_data() -> None:
    rows = [
        stock_strength(prices(10), {"code": "A", "category": "新能源"}),
        stock_strength(pd.DataFrame(), {"code": "B", "category": "光伏"}),
    ]
    ranked = rank_strength(rows)
    assert ranked.iloc[0]["score"] >= ranked.iloc[-1]["score"]


def test_category_aggregation() -> None:
    ranked = rank_strength(
        [
            stock_strength(prices(10), {"code": "A", "category": "新能源"}),
            stock_strength(prices(20), {"code": "B", "category": "新能源"}),
        ]
    )
    category = category_strength(ranked)
    assert category.iloc[0]["category"] == "新能源"
    assert category.iloc[0]["rising_stocks"] == 2
