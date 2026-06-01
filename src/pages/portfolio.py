from __future__ import annotations

from datetime import timedelta

import streamlit as st

from src import database
from src.data_fetcher import BENCHMARKS, fetch_benchmark_prices, fetch_daily_prices
from src.pages.common import CATEGORIES, today
from src.portfolio.rebalance import run_portfolio_backtest
from src.portfolio.risk import category_exposure, single_stock_exposure, validate_limits
from src.strength import rank_strength, stock_strength


def portfolio_page() -> None:
    watchlist = database.get_watchlist()
    if watchlist.empty:
        st.info("暂无自选股。")
        return

    with st.form("portfolio_lab"):
        cols = st.columns(4)
        category = cols[0].selectbox("分类", ["全部"] + CATEGORIES)
        method_label = cols[1].selectbox("构建方式", ["等权", "分数加权", "风险调整"])
        frequency_label = cols[2].selectbox("再平衡频率", ["monthly", "weekly", "quarterly"])
        benchmark = cols[3].selectbox("基准", list(BENCHMARKS))
        selected = watchlist if category == "全部" else watchlist[watchlist["category"] == category]
        selected_codes = st.multiselect(
            "股票池",
            selected["code"].tolist(),
            default=selected["code"].head(8).tolist(),
        )
        cols = st.columns(4)
        initial_capital = cols[0].number_input("初始资金", min_value=1000.0, value=100000.0)
        max_position = cols[1].number_input("单票上限", min_value=0.01, max_value=1.0, value=0.2)
        max_category = cols[2].number_input("分类上限", min_value=0.01, max_value=1.0, value=0.4)
        cash_reserve = cols[3].number_input("现金保留", min_value=0.0, max_value=0.9, value=0.1)
        allow_mock = st.checkbox("失败时使用 Mock 数据", value=True)
        submitted = st.form_submit_button("运行组合模拟")

    if not submitted:
        return

    subset = watchlist[watchlist["code"].isin(selected_codes)]
    if subset.empty:
        st.error("请至少选择一只股票。")
        return

    start_date = (today() - timedelta(days=180)).isoformat()
    end_date = today().isoformat()
    price_map = {}
    rows = []
    failures = []
    with st.spinner("正在构建组合..."):
        for item in subset.to_dict("records"):
            try:
                prices, _ = fetch_daily_prices(
                    item["code"], start_date, end_date, allow_mock=allow_mock
                )
                price_map[item["code"]] = prices
                rows.append(
                    stock_strength(
                        prices,
                        {"code": item["code"], "name": item["name"], "category": item["category"]},
                    )
                )
            except Exception as exc:
                failures.append(f"{item['code']}: {exc}")

    universe = rank_strength(rows)
    if universe.empty:
        st.error("没有可用于组合模拟的数据。")
        return

    method = {"等权": "equal", "分数加权": "score", "风险调整": "risk_adjusted"}[method_label]
    benchmark_prices, benchmark_source, _ = fetch_benchmark_prices(
        benchmark,
        start_date,
        end_date,
        allow_mock=True,
    )
    result = run_portfolio_backtest(
        price_map,
        universe,
        method=method,
        initial_capital=initial_capital,
        max_position=max_position,
        max_category_exposure=max_category,
        cash_reserve=cash_reserve,
        frequency=frequency_label,
        benchmark_prices=benchmark_prices,
    )
    _render_result(result, benchmark_source)
    if failures:
        st.warning("部分股票数据不可用：" + "；".join(failures[:5]))


def _render_result(result: dict, benchmark_source: str) -> None:
    metrics = result["metrics"]
    cols = st.columns(4)
    cols[0].metric("组合收益", f"{metrics['portfolio_return']:.2%}")
    cols[1].metric("年化收益", f"{metrics['annualized_return']:.2%}")
    cols[2].metric("最大回撤", f"{metrics['max_drawdown']:.2%}")
    cols[3].metric("超额收益", f"{metrics['excess_return']:.2%}")
    cols = st.columns(4)
    cols[0].metric("波动率", f"{metrics['volatility']:.2%}")
    cols[1].metric("Sharpe-like", f"{metrics['sharpe_like']:.2f}")
    cols[2].metric("换手率", f"{metrics['turnover']:.2%}")
    cols[3].metric("基准收益", f"{metrics['benchmark_return']:.2%}")
    st.caption(f"基准数据来源：{benchmark_source}")

    st.subheader("目标权重")
    weights = result["weights"]
    st.dataframe(weights, use_container_width=True, hide_index=True)
    for warning in validate_limits(weights):
        st.warning(warning)

    left, right = st.columns(2)
    with left:
        st.subheader("分类暴露")
        st.dataframe(category_exposure(weights), use_container_width=True, hide_index=True)
    with right:
        st.subheader("单票暴露")
        st.dataframe(single_stock_exposure(weights), use_container_width=True, hide_index=True)

    st.subheader("组合权益曲线")
    st.line_chart(result["equity_curve"].set_index("trade_date")["equity"])
    if not result["benchmark_curve"].empty:
        st.subheader("基准权益曲线")
        st.line_chart(result["benchmark_curve"].set_index("trade_date")["equity"])
