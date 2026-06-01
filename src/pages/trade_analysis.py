from __future__ import annotations

import streamlit as st

from src import database
from src.analyzer import analyze_trade
from src.data_fetcher import DataFetchError, fetch_daily_prices
from src.pages.common import benchmark_select, display_error, render_analysis


def trade_analysis_page() -> None:
    trades = database.get_trades()
    if trades.empty:
        st.info("暂无模拟交易。")
        return

    options = {
        f"#{row.id} {row.code} {row.buy_date} {row.name or ''}": int(row.id)
        for row in trades.itertuples()
    }
    selected = st.selectbox("选择交易", list(options.keys()))
    benchmark_name = benchmark_select()
    trade = database.get_trade(options[selected])
    if trade is None:
        st.error("交易不存在。")
        return

    tags = database.get_trade_tags(int(trade["id"]))
    if tags:
        st.caption("标签：" + "、".join(tags))

    try:
        prices, source = fetch_daily_prices(trade["code"], trade["buy_date"], trade["end_date"])
        analysis = analyze_trade(
            prices, float(trade["buy_price"]), int(trade["quantity"]), trade["buy_date"]
        )
        if analysis["actual_start_date"] != trade.get("actual_start_date"):
            database.update_trade_actual_start_date(int(trade["id"]), analysis["actual_start_date"])
        st.caption(f"数据来源：{source}")
        render_analysis(analysis, float(trade["buy_price"]), trade["buy_date"], benchmark_name)
    except (ValueError, DataFetchError) as exc:
        display_error(exc)
