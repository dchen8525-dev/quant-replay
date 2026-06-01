from __future__ import annotations

from datetime import timedelta

import streamlit as st

from src import database
from src.data_fetcher import BENCHMARKS, fetch_daily_prices
from src.pages.common import today
from src.strategy_lab.experiment import (
    anti_overfitting_warnings,
    experiment_history,
    save_experiment,
    save_experiment_result,
)
from src.strategy_lab.optimizer import run_parameter_grid
from src.strategy_lab.registry import get_strategy, list_strategies
from src.strategy_lab.walk_forward import walk_forward_test


def strategy_lab_page() -> None:
    watchlist = database.get_watchlist()
    if watchlist.empty:
        st.info("暂无自选股。")
        return

    with st.form("strategy_lab"):
        cols = st.columns(4)
        name = cols[0].text_input("实验名称", value="Strategy Experiment")
        strategy_name = cols[1].selectbox("策略", list_strategies())
        benchmark = cols[2].selectbox("基准", list(BENCHMARKS))
        initial_capital = cols[3].number_input("初始资金", min_value=1000.0, value=100000.0)
        selected_codes = st.multiselect(
            "股票池",
            watchlist["code"].tolist(),
            default=watchlist["code"].head(1).tolist(),
        )
        cols = st.columns(3)
        start_date = cols[0].date_input("开始日期", value=today() - timedelta(days=240))
        end_date = cols[1].date_input("结束日期", value=today())
        train_ratio = cols[2].slider("训练集比例", 0.5, 0.9, 0.7)
        params = _params_input(strategy_name)
        run_grid = st.checkbox("运行参数网格", value=True)
        submitted = st.form_submit_button("运行实验")

    if submitted:
        if not selected_codes:
            st.error("请至少选择一个标的。")
            return
        try:
            prices, _ = fetch_daily_prices(
                selected_codes[0],
                start_date.isoformat(),
                end_date.isoformat(),
                allow_mock=True,
            )
            if run_grid:
                grid = get_strategy(strategy_name).params
                comparison = run_parameter_grid(prices, strategy_name, grid, initial_capital)
                st.subheader("参数比较")
                st.dataframe(comparison, use_container_width=True, hide_index=True)
                best_params = comparison.iloc[0]["params"] if not comparison.empty else params
            else:
                comparison = None
                best_params = params

            wf = walk_forward_test(
                prices,
                strategy_name,
                best_params,
                train_ratio=train_ratio,
                initial_capital=initial_capital,
            )
            exp_id = save_experiment(
                name,
                strategy_name,
                best_params,
                selected_codes,
                start_date.isoformat(),
                end_date.isoformat(),
                benchmark,
            )
            save_experiment_result(exp_id, wf["test_metrics"], wf)
            _render_walk_forward(wf)
            for warning in anti_overfitting_warnings(
                best_params,
                wf["test_metrics"],
                wf["train_rows"],
                wf["test_rows"],
            ):
                st.warning(warning)
            st.success(f"实验已保存 #{exp_id}")
        except Exception as exc:
            st.error(str(exc))

    st.subheader("实验历史")
    st.dataframe(experiment_history(), use_container_width=True, hide_index=True)


def _params_input(strategy_name: str) -> dict:
    spec = get_strategy(strategy_name)
    st.caption(spec.description)
    params = {}
    cols = st.columns(max(1, min(4, len(spec.params))))
    for index, (key, values) in enumerate(spec.params.items()):
        default = values[0]
        if all(isinstance(value, int) for value in values):
            params[key] = cols[index % len(cols)].number_input(key, value=int(default), step=1)
        elif all(isinstance(value, (int, float)) for value in values):
            params[key] = cols[index % len(cols)].number_input(
                key,
                value=float(default),
                format="%.3f",
            )
        else:
            params[key] = cols[index % len(cols)].selectbox(key, values)
    return params


def _render_walk_forward(result: dict) -> None:
    st.subheader("Walk-forward")
    cols = st.columns(4)
    cols[0].metric("训练收益", f"{result['train_metrics']['total_return']:.2%}")
    cols[1].metric("测试收益", f"{result['test_metrics']['total_return']:.2%}")
    cols[2].metric("测试回撤", f"{result['test_metrics']['max_drawdown']:.2%}")
    cols[3].metric("测试交易数", result["test_metrics"]["trade_count"])
