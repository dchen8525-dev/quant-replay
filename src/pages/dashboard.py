from __future__ import annotations

import streamlit as st

from src import database
from src.analyzer import analyze_many, tag_statistics
from src.charts import distribution_chart


def dashboard_page() -> None:
    trades = database.get_trades()
    if trades.empty:
        st.info("暂无模拟交易。")
        return

    analyzed = analyze_many(trades, lambda c, s, e: database.get_prices(c, s, e))
    valid = analyzed.dropna(subset=["final_return"])
    cols = st.columns(5)
    cols[0].metric("总交易", len(trades))
    cols[1].metric("胜率", f"{(valid['final_return'] > 0).mean():.1%}" if not valid.empty else "-")
    cols[2].metric("平均收益", f"{valid['final_return'].mean():.1%}" if not valid.empty else "-")
    cols[3].metric(
        "平均最大浮亏", f"{valid['max_floating_loss'].mean():.1%}" if not valid.empty else "-"
    )
    cols[4].metric("已分析", len(valid))

    if valid.empty:
        st.info("已有交易但缺少可分析的缓存行情，请先打开交易分析页拉取行情。")
        return

    best = valid.loc[valid["final_return"].idxmax()]
    worst = valid.loc[valid["final_return"].idxmin()]
    st.caption(f"最佳交易：{best['code']} {best.get('name', '')} {best['final_return']:.1%}")
    st.caption(f"最差交易：{worst['code']} {worst.get('name', '')} {worst['final_return']:.1%}")

    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            distribution_chart(valid["final_return"], "收益分布"), use_container_width=True
        )
    with right:
        industry = valid.groupby("industry", dropna=False).size().reset_index(name="count")
        st.bar_chart(industry, x="industry", y="count")

    st.subheader("标签表现统计")
    tag_stats = tag_statistics(analyzed, database.get_all_trade_tags())
    if tag_stats.empty:
        st.info("暂无标签统计。")
    else:
        st.dataframe(tag_stats, use_container_width=True, hide_index=True)
