from __future__ import annotations

from datetime import timedelta

import streamlit as st

from src import database
from src.data_fetcher import fetch_daily_prices
from src.factors.engine import build_factor_table, rank_factor_table
from src.factors.evaluator import evaluate_all_factors, evaluate_factor
from src.factors.library import FACTOR_NAMES
from src.pages.common import CATEGORIES, today


def factors_page() -> None:
    watchlist = database.get_watchlist()
    if watchlist.empty:
        st.info("暂无自选股。")
        return

    cols = st.columns(4)
    category = cols[0].selectbox("分类", ["全部"] + CATEGORIES)
    factor_name = cols[1].selectbox("因子", FACTOR_NAMES)
    lookback_days = cols[2].number_input("回看天数", min_value=80, value=140)
    allow_mock = cols[3].checkbox("失败时使用 Mock", value=True)

    selected = watchlist if category == "全部" else watchlist[watchlist["category"] == category]
    if selected.empty:
        st.info("当前分类没有自选股。")
        return

    if st.button("运行因子研究"):
        start_date = (today() - timedelta(days=int(lookback_days))).isoformat()
        end_date = today().isoformat()
        price_map = {}
        failures = []
        with st.spinner("正在计算因子..."):
            for item in selected.to_dict("records"):
                try:
                    prices, _ = fetch_daily_prices(
                        item["code"],
                        start_date,
                        end_date,
                        allow_mock=allow_mock,
                    )
                    price_map[item["code"]] = prices
                except Exception as exc:
                    failures.append(f"{item['code']}: {exc}")

        table = build_factor_table(price_map, selected)
        if table.empty:
            st.error("没有可用于因子研究的数据。")
            return

        ranked = rank_factor_table(table, factor_name)
        summary = evaluate_all_factors(table)
        evaluation = evaluate_factor(table, factor_name)

        st.subheader("因子排名")
        st.dataframe(ranked, use_container_width=True, hide_index=True)
        st.subheader("Factor IC Summary")
        st.dataframe(summary, use_container_width=True, hide_index=True)

        st.subheader("因子分位收益")
        quantiles = evaluation["quantiles"]
        if quantiles.empty:
            st.info("样本不足，无法形成分位数组。")
        else:
            st.dataframe(quantiles, use_container_width=True, hide_index=True)
            st.bar_chart(quantiles.set_index("quantile")["average_return"])

        if not summary.empty:
            best = summary.iloc[0]
            worst = summary.sort_values("rank_ic_20d").iloc[0]
            st.caption(f"Best factor: {best['factor']}；Worst factor: {worst['factor']}")

        if failures:
            st.warning("部分股票数据不可用：" + "；".join(failures[:5]))
