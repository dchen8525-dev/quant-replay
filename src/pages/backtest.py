from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

from src.backtest.engine import run_backtest
from src.data_fetcher import BENCHMARKS, fetch_benchmark_prices, fetch_daily_prices
from src.pages.common import today
from src.utils import validate_stock_code


def backtest_page() -> None:
    with st.form("backtest_form"):
        cols = st.columns(4)
        code = cols[0].text_input("股票代码", value="002594")
        name = cols[1].text_input("股票名称")
        start_date = cols[2].date_input("开始日期", value=today() - timedelta(days=180))
        end_date = cols[3].date_input("结束日期", value=today())
        cols = st.columns(4)
        initial_capital = cols[0].number_input("初始资金", min_value=1000.0, value=100000.0)
        commission_rate = cols[1].number_input("佣金率", min_value=0.0, value=0.0003, format="%.5f")
        slippage_rate = cols[2].number_input("滑点率", min_value=0.0, value=0.0005, format="%.5f")
        benchmark = cols[3].selectbox("基准", list(BENCHMARKS))
        strategy = st.selectbox("策略", ["Moving Average Cross", "Breakout", "Mean Reversion"])
        params = _strategy_params(strategy)
        allow_mock = st.checkbox("真实数据失败时使用 Mock 数据", value=False)
        submitted = st.form_submit_button("运行回测")

    if not submitted:
        return
    valid, normalized = validate_stock_code(code)
    if not valid:
        st.error("股票代码格式错误，请输入 6 位 A股代码，例如 002594。")
        return

    try:
        prices, source = fetch_daily_prices(
            normalized,
            start_date.isoformat(),
            end_date.isoformat(),
            allow_mock=allow_mock,
        )
        benchmark_prices, benchmark_source, _ = fetch_benchmark_prices(
            benchmark,
            start_date.isoformat(),
            end_date.isoformat(),
            allow_mock=True,
        )
        result = run_backtest(
            prices,
            strategy,
            params,
            initial_capital,
            commission_rate,
            slippage_rate,
            benchmark_prices,
        )
        st.caption(f"{name or normalized} 数据来源：{source}；基准来源：{benchmark_source}")
        _render_result(result)
    except Exception as exc:
        st.error(str(exc))


def _strategy_params(strategy: str) -> dict:
    cols = st.columns(3)
    if strategy == "Moving Average Cross":
        return {
            "ma_short": cols[0].number_input("短均线", min_value=2, value=5),
            "ma_long": cols[1].number_input("长均线", min_value=3, value=20),
        }
    if strategy == "Breakout":
        return {
            "window": cols[0].number_input("突破周期", min_value=2, value=20),
            "ma_exit": cols[1].number_input("退出均线", min_value=2, value=10),
        }
    return {
        "ma": cols[0].number_input("均线", min_value=2, value=20),
        "threshold": cols[1].number_input("偏离阈值", value=-0.05, format="%.3f"),
    }


def _render_result(result) -> None:
    metrics = result.metrics
    cols = st.columns(4)
    cols[0].metric("最终权益", f"{metrics['final_equity']:.2f}")
    cols[1].metric("总收益", f"{metrics['total_return']:.2%}")
    cols[2].metric("基准收益", f"{metrics['benchmark_return']:.2%}")
    cols[3].metric("超额收益", f"{metrics['excess_return']:.2%}")
    cols = st.columns(4)
    cols[0].metric("年化收益", f"{metrics['annualized_return']:.2%}")
    cols[1].metric("最大回撤", f"{metrics['max_drawdown']:.2%}")
    cols[2].metric("胜率", f"{metrics['win_rate']:.2%}")
    cols[3].metric("交易次数", metrics["trade_count"])

    equity = result.equity_curve.set_index("trade_date")["equity"]
    st.line_chart(equity)
    if not result.benchmark_curve.empty:
        st.line_chart(result.benchmark_curve.set_index("trade_date")["equity"])
    drawdown = equity / equity.cummax() - 1
    st.area_chart(pd.DataFrame({"drawdown": drawdown}))
    st.dataframe(result.trades, use_container_width=True, hide_index=True)
