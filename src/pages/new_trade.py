from __future__ import annotations

from datetime import timedelta

import streamlit as st

from src import database
from src.analyzer import analyze_trade
from src.data_fetcher import DataFetchError, fetch_daily_prices
from src.pages.common import (
    DEFAULT_TAGS,
    display_error,
    parse_custom_tags,
    render_analysis,
    today,
)
from src.utils import validate_stock_code


def new_trade_page() -> None:
    with st.form("new_trade"):
        cols = st.columns(3)
        code = cols[0].text_input("股票代码", value="002594")
        name = cols[1].text_input("股票名称")
        industry = cols[2].text_input("行业")
        cols = st.columns(4)
        buy_date = cols[0].date_input("买入日期", value=today() - timedelta(days=30))
        end_date = cols[1].date_input("结束日期", value=today())
        buy_price = cols[2].number_input("买入价格", min_value=0.01, step=0.01)
        quantity = cols[3].number_input("数量", min_value=1, step=100)
        reason = st.text_area("买入理由")
        selected_tags = st.multiselect("标签", DEFAULT_TAGS)
        custom_tags = st.text_input("自定义标签（逗号分隔）")
        cols = st.columns([1, 2, 1])
        confidence = cols[0].slider("信心", 1, 5, 3)
        note = cols[1].text_input("备注")
        benchmark_name = cols[2].selectbox(
            "基准指数", ["沪深300", "中证500", "上证指数", "深证成指", "创业板指"]
        )
        allow_mock = st.checkbox("真实数据失败时使用 Mock 数据", value=False)
        submitted = st.form_submit_button("保存并分析")

    if not submitted:
        return

    valid, normalized = validate_stock_code(code)
    if not valid:
        st.error("股票代码格式错误，请输入 6 位 A股代码，例如 002594。")
        return
    if end_date < buy_date:
        st.error("结束日期不能早于买入日期。")
        return
    if end_date > today():
        st.error("结束日期不能晚于今天。")
        return

    try:
        prices, source = fetch_daily_prices(
            normalized,
            buy_date.isoformat(),
            end_date.isoformat(),
            allow_mock=allow_mock,
        )
        analysis = analyze_trade(prices, float(buy_price), int(quantity), buy_date.isoformat())
        trade_id = database.add_trade(
            {
                "code": normalized,
                "name": name,
                "industry": industry,
                "buy_date": buy_date.isoformat(),
                "actual_start_date": analysis["actual_start_date"],
                "buy_price": float(buy_price),
                "quantity": int(quantity),
                "end_date": end_date.isoformat(),
                "reason": reason,
                "confidence": int(confidence),
                "note": note,
            }
        )
        database.add_trade_tags(trade_id, selected_tags + parse_custom_tags(custom_tags))
        st.success(f"已保存交易 #{trade_id}，数据来源：{source}")
        render_analysis(analysis, float(buy_price), buy_date.isoformat(), benchmark_name)
    except (ValueError, DataFetchError) as exc:
        display_error(exc)
