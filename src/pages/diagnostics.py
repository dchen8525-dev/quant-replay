from __future__ import annotations

import io
from datetime import timedelta

import pandas as pd
import streamlit as st

from src import database
from src.data_quality import validate_price_df
from src.pages.common import today
from src.providers import (
    AkshareEastmoneyProvider,
    AkshareIndexTencentProvider,
    AkshareTencentProvider,
    MockProvider,
)
from src.release import read_version, release_readiness_report
from src.utils import validate_stock_code


def diagnostics_page() -> None:
    st.subheader("Release Readiness")
    st.caption(f"当前版本：{read_version()}")
    release_report = release_readiness_report()
    st.dataframe(release_report, use_container_width=True, hide_index=True)
    if (release_report["status"] == "pass").all():
        st.success("发布检查通过。")
    else:
        st.warning("发布检查存在未完成项。")

    st.subheader("Provider 测试")
    cols = st.columns(3)
    code = cols[0].text_input("测试代码", value="002594")
    start_date = cols[1].date_input("开始日期", value=today() - timedelta(days=10))
    end_date = cols[2].date_input("结束日期", value=today())

    if st.button("测试全部 Provider"):
        results = []
        for provider in [AkshareTencentProvider(), AkshareEastmoneyProvider(), MockProvider()]:
            results.append(
                _test_provider(provider, code, start_date.isoformat(), end_date.isoformat())
            )
        st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)

    st.subheader("指数 Provider 测试")
    if st.button("测试沪深300"):
        result = _test_provider(
            AkshareIndexTencentProvider(), "sh000300", start_date.isoformat(), end_date.isoformat()
        )
        st.dataframe(pd.DataFrame([result]), use_container_width=True, hide_index=True)

    st.subheader("缓存状态")
    summary = database.cache_summary()
    st.dataframe(summary, use_container_width=True, hide_index=True)
    st.download_button(
        "Export price cache CSV", _csv_bytes(database.price_cache()), "price_cache.csv", "text/csv"
    )
    cache_code = st.text_input("清除缓存代码（留空清除全部）")
    left, right = st.columns(2)
    if left.button("clear cache for selected code"):
        database.clear_price_cache(cache_code.strip() or None)
        st.rerun()
    if right.button("refresh cache summary"):
        st.rerun()

    st.subheader("数据质量")
    quality_code = st.text_input("质量检查代码", value="002594")
    if st.button("检查缓存行情质量"):
        prices = database.get_prices(quality_code.strip(), "1900-01-01", "2999-12-31")
        warnings = validate_price_df(prices)
        if warnings:
            for warning in warnings:
                st.warning(warning)
        else:
            st.success("缓存行情未发现明显质量问题。")

    st.subheader("数据库备份")
    if database.DB_PATH.exists():
        st.download_button(
            "Export full SQLite database backup",
            database.DB_PATH.read_bytes(),
            "quant_replay.db",
            "application/octet-stream",
        )
    else:
        st.info("数据库文件尚未创建。")

    st.subheader("Provider 日志")
    logs = database.provider_logs()
    st.dataframe(logs, use_container_width=True, hide_index=True)
    if st.button("clear all provider logs"):
        database.clear_provider_logs()
        st.rerun()


def _test_provider(provider, code: str, start_date: str, end_date: str) -> dict:
    test_code = code
    if provider.name in {"tencent", "eastmoney", "mock"}:
        valid, normalized = validate_stock_code(code)
        if not valid:
            return {
                "provider": provider.name,
                "status": "error",
                "row_count": 0,
                "first_date": None,
                "last_date": None,
                "error_message": "股票代码格式错误，请输入 6 位 A股代码，例如 002594。",
            }
        test_code = normalized

    try:
        df = provider.fetch_daily(test_code, start_date, end_date)
        status = "ok" if not df.empty else "empty"
        database.log_provider(provider.name, test_code, status, f"{len(df)} rows")
        return {
            "provider": provider.name,
            "status": status,
            "row_count": len(df),
            "first_date": None if df.empty else df.iloc[0]["trade_date"],
            "last_date": None if df.empty else df.iloc[-1]["trade_date"],
            "error_message": "",
        }
    except Exception as exc:
        message = str(exc)
        if provider.name == "eastmoney" and "SSL" in message.upper():
            message = "东方财富数据源在当前网络环境下 SSL 连接失败，已忽略该错误。"
        database.log_provider(provider.name, test_code, "error", message)
        return {
            "provider": provider.name,
            "status": "error",
            "row_count": 0,
            "first_date": None,
            "last_date": None,
            "error_message": message,
        }


def _csv_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8-sig")
