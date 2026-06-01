from __future__ import annotations

import streamlit as st

from src import database
from src.analyzer import analyze_many, tag_statistics
from src.review import by_category, by_confidence, learning_insights, overall_report


def review_page() -> None:
    trades = database.get_trades()
    if trades.empty:
        st.info("暂无模拟交易。")
        return

    analyzed = analyze_many(trades, lambda c, s, e: database.get_prices(c, s, e))
    tags = database.get_all_trade_tags()
    overall = overall_report(analyzed)
    cols = st.columns(4)
    cols[0].metric("总交易", overall["total_trades"])
    cols[1].metric("胜率", f"{overall['win_rate']:.2%}")
    cols[2].metric("平均收益", f"{overall['average_return']:.2%}")
    cols[3].metric("收益中位数", f"{overall['median_return']:.2%}")
    st.caption(f"最佳交易：{overall['best_trade']}；最差交易：{overall['worst_trade']}")

    st.subheader("按标签")
    st.dataframe(tag_statistics(analyzed, tags), use_container_width=True, hide_index=True)
    st.subheader("按分类")
    st.dataframe(by_category(analyzed), use_container_width=True, hide_index=True)
    st.subheader("按信心")
    st.dataframe(by_confidence(analyzed), use_container_width=True, hide_index=True)
    st.subheader("Learning Insights")
    for line in learning_insights(analyzed, tags):
        st.write(line)
