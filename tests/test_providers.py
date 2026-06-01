from __future__ import annotations

import pandas as pd

from src.providers.akshare_eastmoney import AkshareEastmoneyProvider
from src.providers.akshare_index_tencent import AkshareIndexTencentProvider
from src.providers.akshare_tencent import AkshareTencentProvider
from src.providers.mock_provider import MockProvider


def test_mock_provider_returns_normalized_data() -> None:
    df = MockProvider().fetch_daily("002594", "2026-05-01", "2026-05-08")
    assert not df.empty
    assert {"trade_date", "open", "high", "low", "close", "volume", "amount"}.issubset(df.columns)


def test_tencent_normalizer() -> None:
    raw = pd.DataFrame(
        [{"date": "2026-05-01", "open": "1", "high": "2", "low": "1", "close": "2", "volume": "3"}]
    )
    df = AkshareTencentProvider()._normalize(raw)
    assert df.iloc[0]["trade_date"] == "2026-05-01"
    assert df.iloc[0]["close"] == 2


def test_eastmoney_normalizer() -> None:
    raw = pd.DataFrame(
        [{"日期": "2026-05-01", "开盘": "1", "最高": "2", "最低": "1", "收盘": "2", "成交量": "3"}]
    )
    df = AkshareEastmoneyProvider()._normalize(raw)
    assert df.iloc[0]["trade_date"] == "2026-05-01"
    assert df.iloc[0]["close"] == 2


def test_index_normalizer() -> None:
    raw = pd.DataFrame(
        [{"date": "2026-05-01", "open": "1", "high": "2", "low": "1", "close": "2", "volume": "3"}]
    )
    df = AkshareIndexTencentProvider()._normalize(raw)
    assert df.iloc[0]["trade_date"] == "2026-05-01"
    assert df.iloc[0]["close"] == 2
