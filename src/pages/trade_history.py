from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from src import database
from src.analyzer import analyze_many
from src.pages.common import parse_custom_tags
from src.utils import validate_stock_code


def trade_history_page() -> None:
    trades = database.get_trades()
    if trades.empty:
        st.info("暂无模拟交易。")
        return

    analyzed = analyze_many(trades, lambda c, s, e: database.get_prices(c, s, e))
    tags = database.get_all_trade_tags()
    if not tags.empty:
        tag_text = tags.groupby("trade_id")["tag"].apply(lambda s: ",".join(s)).reset_index()
        analyzed = analyzed.merge(tag_text, left_on="id", right_on="trade_id", how="left")
    columns = [
        "code",
        "name",
        "buy_date",
        "buy_price",
        "quantity",
        "end_date",
        "final_return",
        "max_floating_loss",
        "reason",
        "confidence",
        "tag",
    ]
    st.dataframe(
        analyzed[[col for col in columns if col in analyzed.columns]],
        use_container_width=True,
        hide_index=True,
    )
    st.download_button(
        "Export trades CSV", _csv_bytes(analyzed), "simulated_trades.csv", "text/csv"
    )

    uploaded = st.file_uploader("Import simulated trades CSV", type=["csv"])
    if uploaded and st.button("导入模拟交易"):
        imported = pd.read_csv(uploaded)
        required = {
            "code",
            "name",
            "industry",
            "buy_date",
            "buy_price",
            "quantity",
            "end_date",
            "reason",
            "confidence",
            "note",
        }
        if not required.issubset(imported.columns):
            st.error("交易 CSV 字段不完整。")
            return
        count = 0
        for row in imported.to_dict("records"):
            valid, normalized = validate_stock_code(str(row.get("code", "")))
            if not valid:
                continue
            try:
                trade_id = database.add_trade(
                    {
                        "code": normalized,
                        "name": str(row.get("name", "")),
                        "industry": str(row.get("industry", "")),
                        "buy_date": str(row.get("buy_date", ""))[:10],
                        "buy_price": float(row.get("buy_price")),
                        "quantity": int(row.get("quantity")),
                        "end_date": str(row.get("end_date", ""))[:10],
                        "reason": str(row.get("reason", "")),
                        "confidence": int(row.get("confidence", 3) or 3),
                        "note": str(row.get("note", "")),
                    }
                )
                if "tags" in imported.columns:
                    database.add_trade_tags(trade_id, parse_custom_tags(str(row.get("tags", ""))))
                count += 1
            except (TypeError, ValueError):
                continue
        st.success(f"已导入 {count} 条模拟交易。")
        st.rerun()


def _csv_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8-sig")
