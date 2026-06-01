from __future__ import annotations

import streamlit as st

from src.account.account import account_summary, equity_curve, validate_buy, validate_sell
from src.account.ledger import add_transaction, get_transactions
from src.account.metrics import current_positions
from src.pages.common import today
from src.utils import validate_stock_code


def account_page() -> None:
    account_name = st.text_input("账户名称", value="default")
    initial_cash = st.number_input("初始现金", min_value=1000.0, value=100000.0)
    transactions = get_transactions(account_name)
    summary = account_summary(transactions, initial_cash)

    cols = st.columns(4)
    cols[0].metric("现金余额", f"{summary['cash_balance']:.2f}")
    cols[1].metric("账户权益", f"{summary['equity']:.2f}")
    cols[2].metric("已实现盈亏", f"{summary['realized_pnl']:.2f}")
    cols[3].metric("未实现盈亏", f"{summary['unrealized_pnl']:.2f}")

    with st.form("account_transaction"):
        cols = st.columns(6)
        trade_date = cols[0].date_input("日期", value=today())
        action = cols[1].selectbox("操作", ["BUY", "SELL"])
        code = cols[2].text_input("代码", value="002594")
        name = cols[3].text_input("名称")
        price = cols[4].number_input("价格", min_value=0.01, value=10.0)
        quantity = cols[5].number_input("数量", min_value=1, value=100)
        commission = st.number_input("佣金", min_value=0.0, value=0.0)
        note = st.text_input("备注")
        submitted = st.form_submit_button("记录交易")

    if submitted:
        valid, normalized = validate_stock_code(code)
        if not valid:
            st.error("股票代码格式错误，请输入 6 位 A股代码，例如 002594。")
        else:
            try:
                positions = current_positions(transactions)
                if action == "BUY":
                    validate_buy(summary["cash_balance"], price, int(quantity), commission)
                else:
                    validate_sell(positions, normalized, int(quantity))
                add_transaction(
                    account_name,
                    trade_date.isoformat(),
                    action,
                    normalized,
                    name,
                    price,
                    int(quantity),
                    commission,
                    note,
                )
                st.success("交易已记录。")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    st.subheader("当前持仓")
    st.dataframe(summary["positions"], use_container_width=True, hide_index=True)
    st.subheader("交易流水")
    st.dataframe(transactions, use_container_width=True, hide_index=True)
    st.subheader("账户权益曲线")
    curve = equity_curve(transactions, initial_cash)
    if not curve.empty and curve.iloc[0]["trade_date"]:
        st.line_chart(curve.set_index("trade_date")["equity"])
