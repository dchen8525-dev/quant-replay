from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from src import database
from src.analyzer import analyze_many, analyze_trade
from src.charts import benchmark_comparison, distribution_chart, drawdown_chart, price_chart, return_chart
from src.data_fetcher import DataFetchError, fetch_daily_prices
from src.utils import normalize_code, validate_stock_code


CATEGORIES = ["新能源", "汽车链", "AI/半导体", "消费成长", "周期化工", "金融情绪", "光伏", "机器人/设备", "其他"]


def main() -> None:
    st.set_page_config(page_title="QuantReplay", layout="wide")
    database.init_db()
    st.title("QuantReplay")

    page = st.sidebar.radio(
        "页面",
        ["Dashboard", "New Simulated Trade", "Trade Analysis", "Trade History", "Watchlist", "Data Diagnostics"],
    )
    if page == "Dashboard":
        dashboard_page()
    elif page == "New Simulated Trade":
        new_trade_page()
    elif page == "Trade Analysis":
        trade_analysis_page()
    elif page == "Trade History":
        trade_history_page()
    elif page == "Watchlist":
        watchlist_page()
    else:
        diagnostics_page()


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
    cols[3].metric("平均最大浮亏", f"{valid['max_floating_loss'].mean():.1%}" if not valid.empty else "-")
    cols[4].metric("已分析", len(valid))

    if not valid.empty:
        best = valid.loc[valid["final_return"].idxmax()]
        worst = valid.loc[valid["final_return"].idxmin()]
        st.caption(f"最佳交易：{best['code']} {best.get('name', '')} {best['final_return']:.1%}")
        st.caption(f"最差交易：{worst['code']} {worst.get('name', '')} {worst['final_return']:.1%}")

        left, right = st.columns(2)
        with left:
            st.plotly_chart(distribution_chart(valid["final_return"], "收益分布"), use_container_width=True)
        with right:
            industry = valid.groupby("industry", dropna=False).size().reset_index(name="count")
            st.bar_chart(industry, x="industry", y="count")


def new_trade_page() -> None:
    with st.form("new_trade"):
        cols = st.columns(3)
        code = cols[0].text_input("股票代码", value="002594")
        name = cols[1].text_input("股票名称")
        industry = cols[2].text_input("行业")
        cols = st.columns(4)
        buy_date = cols[0].date_input("买入日期", value=date.today() - timedelta(days=30))
        end_date = cols[1].date_input("结束日期", value=date.today())
        buy_price = cols[2].number_input("买入价格", min_value=0.01, step=0.01)
        quantity = cols[3].number_input("数量", min_value=1, step=100)
        reason = st.text_area("买入理由")
        cols = st.columns([1, 3])
        confidence = cols[0].slider("信心", 1, 5, 3)
        note = cols[1].text_input("备注")
        allow_mock = st.checkbox("真实数据失败时使用 Mock 数据", value=False)
        submitted = st.form_submit_button("保存并分析")

    if not submitted:
        return

    valid, normalized = validate_stock_code(code)
    if not valid:
        st.error(normalized)
        return
    if end_date < buy_date:
        st.error("结束日期不能早于买入日期。")
        return
    if end_date > date.today():
        st.error("结束日期不能晚于今天。")
        return

    try:
        prices, source = fetch_daily_prices(normalized, buy_date.isoformat(), end_date.isoformat(), allow_mock=allow_mock)
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
        st.success(f"已保存交易 #{trade_id}，数据来源：{source}")
        render_analysis(analysis, float(buy_price), buy_date.isoformat())
    except (ValueError, DataFetchError) as exc:
        st.error(str(exc))


def trade_analysis_page() -> None:
    trades = database.get_trades()
    if trades.empty:
        st.info("暂无模拟交易。")
        return

    options = {f"#{row.id} {row.code} {row.buy_date} {row.name or ''}": int(row.id) for row in trades.itertuples()}
    selected = st.selectbox("选择交易", list(options.keys()))
    trade = database.get_trade(options[selected])
    if trade is None:
        st.error("交易不存在。")
        return

    try:
        prices, source = fetch_daily_prices(trade["code"], trade["buy_date"], trade["end_date"])
        analysis = analyze_trade(prices, float(trade["buy_price"]), int(trade["quantity"]), trade["buy_date"])
        st.caption(f"数据来源：{source}")
        render_analysis(analysis, float(trade["buy_price"]), trade["buy_date"])
    except (ValueError, DataFetchError) as exc:
        st.error(str(exc))


def render_analysis(analysis: dict, buy_price: float, buy_date: str) -> None:
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
    st.plotly_chart(price_chart(series, buy_price, buy_date), use_container_width=True)
    left, right = st.columns(2)
    with left:
        st.plotly_chart(return_chart(series), use_container_width=True)
    with right:
        st.plotly_chart(drawdown_chart(series), use_container_width=True)
    st.plotly_chart(benchmark_comparison(series), use_container_width=True)

    st.subheader("止损模拟")
    st.dataframe(pd.DataFrame(analysis["stop_loss"]), use_container_width=True, hide_index=True)


def trade_history_page() -> None:
    trades = database.get_trades()
    if trades.empty:
        st.info("暂无模拟交易。")
        return
    analyzed = analyze_many(trades, lambda c, s, e: database.get_prices(c, s, e))
    columns = ["code", "name", "buy_date", "buy_price", "quantity", "end_date", "final_return", "max_floating_loss", "reason", "confidence"]
    st.dataframe(analyzed[[col for col in columns if col in analyzed.columns]], use_container_width=True, hide_index=True)


def watchlist_page() -> None:
    with st.form("watchlist_form"):
        cols = st.columns(5)
        code = cols[0].text_input("代码")
        name = cols[1].text_input("名称")
        industry = cols[2].text_input("行业")
        category = cols[3].selectbox("分类", CATEGORIES)
        priority = cols[4].number_input("优先级", min_value=1, max_value=5, value=3)
        note = st.text_input("备注")
        submitted = st.form_submit_button("添加或更新")
    if submitted:
        valid, normalized = validate_stock_code(code)
        if valid:
            database.upsert_watchlist(
                {"code": normalized, "name": name, "industry": industry, "category": category, "priority": int(priority), "note": note}
            )
            st.success("已保存。")
        else:
            st.error(normalized)

    watchlist = database.get_watchlist()
    st.dataframe(watchlist, use_container_width=True, hide_index=True)
    remove_code = st.text_input("删除代码")
    if st.button("删除"):
        normalized = normalize_code(remove_code)
        database.delete_watchlist(normalized)
        st.rerun()


def diagnostics_page() -> None:
    st.subheader("Provider 状态")
    code = st.text_input("测试代码", value="002594")
    cols = st.columns(2)
    if cols[0].button("测试 Tencent"):
        _test_provider(code, "tencent")
    if cols[1].button("测试 Eastmoney"):
        _test_provider(code, "eastmoney")

    st.subheader("缓存状态")
    st.dataframe(database.cache_summary(), use_container_width=True, hide_index=True)
    st.subheader("Provider 日志")
    st.dataframe(database.provider_logs(), use_container_width=True, hide_index=True)


def _test_provider(code: str, provider_name: str) -> None:
    from src.providers import AkshareEastmoneyProvider, AkshareTencentProvider

    valid, normalized = validate_stock_code(code)
    if not valid:
        st.error(normalized)
        return
    provider = AkshareTencentProvider() if provider_name == "tencent" else AkshareEastmoneyProvider()
    try:
        df = provider.fetch_daily(normalized, (date.today() - timedelta(days=10)).isoformat(), date.today().isoformat())
        database.log_provider(provider.name, normalized, "ok", f"{len(df)} rows")
        st.success(f"{provider.name}: {len(df)} rows")
        st.dataframe(df.tail(), use_container_width=True, hide_index=True)
    except Exception as exc:
        database.log_provider(provider.name, normalized, "error", str(exc))
        st.error(f"{provider.name}: {exc}")


if __name__ == "__main__":
    main()
