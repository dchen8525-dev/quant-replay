from __future__ import annotations

from datetime import timedelta

import streamlit as st

from src import database
from src.data_fetcher import fetch_daily_prices
from src.pages.common import CATEGORIES, today
from src.strength import category_strength, rank_strength, stock_strength


def strength_page() -> None:
    watchlist = database.get_watchlist()
    if watchlist.empty:
        st.info("暂无自选股。")
        return

    category = st.selectbox("分类", ["全部"] + CATEGORIES)
    minimum_score = st.slider("最低分", 0, 100, 0)
    only_rising = st.checkbox("只看上升趋势", value=False)

    rows = []
    start_date = (today() - timedelta(days=120)).isoformat()
    end_date = today().isoformat()
    for item in watchlist.to_dict("records"):
        if category != "全部" and item.get("category") != category:
            continue
        try:
            prices, _ = fetch_daily_prices(item["code"], start_date, end_date, allow_mock=True)
            rows.append(
                stock_strength(
                    prices,
                    {"code": item["code"], "name": item["name"], "category": item["category"]},
                )
            )
        except Exception:
            continue

    ranked = rank_strength(rows)
    if ranked.empty:
        st.info("暂无可计算强度的数据。")
        return
    ranked = ranked[ranked["score"] >= minimum_score]
    if only_rising:
        ranked = ranked[ranked["trend"] == "rising"]
    columns = [
        "rank",
        "code",
        "name",
        "category",
        "5d_return",
        "20d_return",
        "60d_return",
        "volatility",
        "distance_to_high",
        "trend",
        "score",
    ]
    st.dataframe(ranked[columns], use_container_width=True, hide_index=True)
    st.subheader("Category Strength")
    category_df = category_strength(ranked)
    st.dataframe(category_df, use_container_width=True, hide_index=True)
    if not category_df.empty:
        st.bar_chart(category_df.set_index("category")["average_20d_return"])
