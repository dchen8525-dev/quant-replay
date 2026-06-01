from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from src import database
from src.pages.common import CATEGORIES
from src.utils import normalize_code, validate_stock_code


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
                {
                    "code": normalized,
                    "name": name,
                    "industry": industry,
                    "category": category,
                    "priority": int(priority),
                    "note": note,
                }
            )
            st.success("已保存。")
        else:
            st.error("股票代码格式错误，请输入 6 位 A股代码，例如 002594。")

    watchlist = database.get_watchlist()
    st.dataframe(watchlist, use_container_width=True, hide_index=True)
    st.download_button("Export watchlist CSV", _csv_bytes(watchlist), "watchlist.csv", "text/csv")

    uploaded = st.file_uploader("Import watchlist CSV", type=["csv"])
    if uploaded and st.button("导入自选股"):
        imported = pd.read_csv(uploaded)
        required = {"code", "name"}
        if not required.issubset(imported.columns):
            st.error("CSV 至少需要 code 和 name 字段。")
        else:
            count = 0
            for row in imported.to_dict("records"):
                valid, normalized = validate_stock_code(str(row.get("code", "")))
                if not valid:
                    continue
                database.upsert_watchlist(
                    {
                        "code": normalized,
                        "name": str(row.get("name", "")),
                        "industry": str(row.get("industry", "")),
                        "category": str(row.get("category", "其他")),
                        "priority": int(row.get("priority", 3) or 3),
                        "note": str(row.get("note", "")),
                    }
                )
                count += 1
            st.success(f"已导入 {count} 条自选股。")
            st.rerun()

    remove_code = st.text_input("删除代码")
    if st.button("删除"):
        database.delete_watchlist(normalize_code(remove_code))
        st.rerun()


def _csv_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8-sig")
