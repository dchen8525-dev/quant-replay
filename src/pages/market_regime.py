from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

from src import database
from src.data_fetcher import BENCHMARKS, fetch_benchmark_prices, fetch_daily_prices
from src.pages.common import today
from src.regime import category_rotation, market_regime_summary, regime_series, rotation_buckets


def market_regime_page() -> None:
    st.subheader("Market Regime")

    cols = st.columns(4)
    benchmark_name = cols[0].selectbox("市场指数", list(BENCHMARKS), index=0)
    lookback_days = cols[1].number_input(
        "回看天数", min_value=90, max_value=720, value=240, step=30
    )
    max_stocks = cols[2].number_input("行业样本上限", min_value=3, max_value=100, value=30, step=5)
    allow_mock = cols[3].checkbox("失败时使用 Mock 数据", value=True)

    start_date = (today() - timedelta(days=int(lookback_days))).isoformat()
    end_date = today().isoformat()

    try:
        benchmark, source, code = fetch_benchmark_prices(
            benchmark_name, start_date, end_date, allow_mock=allow_mock
        )
    except Exception as exc:
        st.error(str(exc))
        return

    summary = market_regime_summary(benchmark)
    cols = st.columns(5)
    cols[0].metric("趋势", summary["trend"])
    cols[1].metric("波动", summary["volatility"])
    cols[2].metric("风险偏好", summary["risk"])
    cols[3].metric("60日回撤", f"{summary['drawdown_60d']:.2%}")
    cols[4].metric("20日波动分位", f"{summary['volatility_percentile']:.0%}")
    st.caption(f"{benchmark_name} {code} 数据来源：{source}")

    series = regime_series(benchmark)
    if not series.empty:
        st.line_chart(series.set_index("trade_date")[["close", "ma20", "ma60"]])
        st.area_chart(series.set_index("trade_date")["drawdown_60d"])

    st.subheader("Industry Rotation")
    watchlist = database.get_watchlist().head(int(max_stocks))
    if watchlist.empty:
        st.info("暂无自选股。")
        return

    prices: dict[str, pd.DataFrame] = {}
    failures: list[str] = []
    for item in watchlist.to_dict("records"):
        try:
            frame, _ = fetch_daily_prices(item["code"], start_date, end_date, allow_mock=allow_mock)
            prices[item["code"]] = frame
        except Exception as exc:
            failures.append(f"{item['code']}: {exc}")

    rotation = category_rotation(prices, watchlist)
    if rotation.empty:
        st.info("暂无可计算行业轮动的数据。")
        if failures:
            st.warning("部分股票数据不可用：" + "；".join(failures[:5]))
        return

    buckets = rotation_buckets(rotation)
    cols = st.columns(3)
    cols[0].write("强势：" + _join_categories(buckets["strong"]))
    cols[1].write("转弱：" + _join_categories(buckets["weakening"]))
    cols[2].write("改善：" + _join_categories(buckets["improving"]))

    display_cols = [
        "category",
        "rotation_state",
        "strength_score",
        "average_5d_return",
        "average_20d_return",
        "average_60d_return",
        "above_ma20_ratio",
        "stock_count",
    ]
    st.dataframe(rotation[display_cols], use_container_width=True, hide_index=True)
    st.bar_chart(rotation.set_index("category")["strength_score"])
    _rotation_chart(rotation)
    if failures:
        st.warning("部分股票数据不可用：" + "；".join(failures[:5]))


def _rotation_chart(rotation: pd.DataFrame) -> None:
    chart = rotation.set_index("category")[
        ["average_5d_return", "average_20d_return", "average_60d_return"]
    ]
    st.line_chart(chart)


def _join_categories(values: list[str]) -> str:
    return "、".join(values) if values else "无"
