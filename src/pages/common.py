from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from src.analyzer import compare_with_benchmark
from src.charts import benchmark_comparison, drawdown_chart, price_chart, return_chart
from src.data_fetcher import BENCHMARKS, DataFetchError, fetch_benchmark_prices

DEFAULT_TAGS = [
    "放量突破",
    "缩量回踩",
    "MA20突破",
    "行业强势",
    "财报超预期",
    "题材追高",
    "低吸",
    "趋势跟随",
    "均值回归",
    "情绪交易",
]

CATEGORIES = [
    "新能源",
    "汽车链",
    "AI/半导体",
    "消费成长",
    "周期化工",
    "金融情绪",
    "光伏",
    "机器人/设备",
    "其他",
]


def display_error(exc: Exception) -> None:
    st.error(str(exc))


def parse_custom_tags(text: str) -> list[str]:
    return [tag.strip() for tag in text.replace("，", ",").split(",") if tag.strip()]


def render_analysis(
    analysis: dict,
    buy_price: float,
    buy_date: str,
    benchmark_name: str = "沪深300",
) -> None:
    cols = st.columns(4)
    cols[0].metric("最终收益", f"{analysis['final_return']:.2%}")
    cols[1].metric("最终盈亏", f"{analysis['final_profit']:.2f}")
    cols[2].metric("最大浮盈", f"{analysis['max_floating_profit']:.2%}")
    cols[3].metric("最大浮亏", f"{analysis['max_floating_loss']:.2%}")
    cols = st.columns(4)
    cols[0].metric("最大回撤", f"{analysis['max_drawdown']:.2%}")
    cols[1].metric("持有交易日", analysis["holding_days"])
    cols[2].metric("最高价", f"{analysis['highest_price_after_buy']:.2f}")
    cols[3].metric("最低价", f"{analysis['lowest_price_after_buy']:.2f}")

    series = analysis["series"]
    benchmark_series = pd.DataFrame()
    try:
        benchmark_prices, benchmark_source, _ = fetch_benchmark_prices(
            benchmark_name,
            str(series.iloc[0]["trade_date"]),
            str(series.iloc[-1]["trade_date"]),
            allow_mock=True,
        )
        comparison = compare_with_benchmark(series, benchmark_prices)
        benchmark_series = comparison["series"]
        cols = st.columns(4)
        cols[0].metric("个股收益", f"{comparison['stock_return']:.2%}")
        cols[1].metric(f"{benchmark_name}收益", f"{comparison['benchmark_return']:.2%}")
        cols[2].metric("超额收益", f"{comparison['excess_return']:.2%}")
        cols[3].metric("跑赢基准", "是" if comparison["outperformed"] else "否")
        st.caption(f"基准数据来源：{benchmark_source}")
    except (ValueError, DataFetchError) as exc:
        st.warning(f"基准比较暂不可用：{exc}")

    st.plotly_chart(price_chart(series, buy_price, buy_date), use_container_width=True)
    left, right = st.columns(2)
    with left:
        st.plotly_chart(return_chart(series), use_container_width=True)
    with right:
        st.plotly_chart(drawdown_chart(series), use_container_width=True)
    st.plotly_chart(benchmark_comparison(series, benchmark_series), use_container_width=True)

    st.subheader("止损模拟")
    st.dataframe(pd.DataFrame(analysis["stop_loss"]), use_container_width=True, hide_index=True)


def benchmark_select(label: str = "基准指数") -> str:
    return st.selectbox(label, list(BENCHMARKS.keys()), index=0)


def today() -> date:
    return date.today()
