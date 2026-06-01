from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

from src import database
from src.data_quality.health import data_health_summary
from src.data_quality.provider_compare import compare_provider_frames
from src.pages.common import today
from src.providers import (
    AkshareEastmoneyProvider,
    AkshareTencentProvider,
    BaostockProvider,
    MockProvider,
)
from src.utils import validate_stock_code

PROVIDERS = {
    "Tencent": AkshareTencentProvider,
    "Eastmoney": AkshareEastmoneyProvider,
    "Baostock": BaostockProvider,
    "Mock": MockProvider,
}


def data_health_page() -> None:
    st.subheader("Provider Compare")
    cols = st.columns(4)
    code = cols[0].text_input("代码", value="002594")
    start_date = cols[1].date_input("开始日期", value=today() - timedelta(days=30))
    end_date = cols[2].date_input("结束日期", value=today())
    left_name = cols[3].selectbox("左侧 Provider", list(PROVIDERS), index=0)
    right_name = st.selectbox("右侧 Provider", list(PROVIDERS), index=1)

    if st.button("Compare Providers"):
        valid, normalized = validate_stock_code(code)
        if not valid:
            st.error("股票代码格式错误，请输入 6 位 A股代码，例如 002594。")
        else:
            left_df, left_error = _fetch_provider(
                left_name,
                normalized,
                start_date.isoformat(),
                end_date.isoformat(),
            )
            right_df, right_error = _fetch_provider(
                right_name,
                normalized,
                start_date.isoformat(),
                end_date.isoformat(),
            )
            st.json(
                {
                    "left_provider": left_name,
                    "right_provider": right_name,
                    "left_error": left_error,
                    "right_error": right_error,
                    **compare_provider_frames(left_df, right_df),
                }
            )

    st.subheader("Cache Coverage")
    summary = database.cache_summary()
    st.dataframe(summary, use_container_width=True, hide_index=True)

    st.subheader("Data Anomalies")
    health_code = st.text_input("缓存健康检查代码", value="002594")
    prices = database.get_prices(health_code.strip(), "1900-01-01", "2999-12-31")
    health = data_health_summary(prices)
    st.json(health)
    if health["warnings"]:
        for warning in health["warnings"]:
            st.warning(warning)


def _fetch_provider(
    provider_name: str,
    code: str,
    start_date: str,
    end_date: str,
) -> tuple[pd.DataFrame, str]:
    provider = PROVIDERS[provider_name]()
    try:
        df = provider.fetch_daily(code, start_date, end_date)
        database.log_provider(provider.name, code, "ok", f"{len(df)} rows")
        return df, ""
    except Exception as exc:
        message = str(exc)
        database.log_provider(provider.name, code, "error", message)
        return pd.DataFrame(), message
