from __future__ import annotations

import pandas as pd
import pytest

from src.data_quality.calendar import missing_observed_dates, observed_trade_dates
from src.data_quality.health import data_health_summary, validate_price_df
from src.data_quality.provider_compare import compare_provider_frames
from src.data_quality.repair import repair_price_df
from src.providers.baostock_provider import BaostockProvider
from src.providers.tushare_provider import TushareProvider


def dirty_prices() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"trade_date": "2026-05-02", "open": 10, "high": 11, "low": 9, "close": 10},
            {"trade_date": "2026-05-01", "open": 0, "high": 11, "low": 9, "close": None},
            {"trade_date": "2026-05-02", "open": 10, "high": 11, "low": 9, "close": 10},
        ]
    )


def clean_prices() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"trade_date": "2026-05-01", "open": 10, "high": 11, "low": 9, "close": 10},
            {"trade_date": "2026-05-02", "open": 11, "high": 12, "low": 10, "close": 11},
        ]
    )


def test_validate_price_df_detects_anomalies() -> None:
    warnings = validate_price_df(dirty_prices())
    assert "duplicate dates" in warnings
    assert "missing close" in warnings
    assert "zero or negative prices" in warnings
    assert "non-monotonic dates" in warnings


def test_repair_price_df() -> None:
    repaired = repair_price_df(dirty_prices())
    assert len(repaired) == 1
    assert repaired.iloc[0]["trade_date"] == "2026-05-02"


def test_calendar_helpers() -> None:
    assert observed_trade_dates(clean_prices()) == ["2026-05-01", "2026-05-02"]
    candidate = clean_prices().tail(1)
    assert missing_observed_dates(clean_prices(), candidate) == ["2026-05-01"]


def test_provider_compare() -> None:
    left = clean_prices()
    right = clean_prices().assign(close=[10.1, 10.9]).tail(1)
    result = compare_provider_frames(left, right)
    assert result["left_rows"] == 2
    assert result["right_rows"] == 1
    assert result["right_missing_dates"] == ["2026-05-01"]
    assert result["max_close_diff"] > 0


def test_data_health_summary() -> None:
    summary = data_health_summary(dirty_prices())
    assert summary["rows"] == 3
    assert summary["duplicate_rows"] == 1
    assert summary["missing_close"] == 1


def test_optional_providers_are_non_blocking(monkeypatch) -> None:
    monkeypatch.delenv("TUSHARE_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="Tushare token"):
        TushareProvider().fetch_daily("002594", "2026-05-01", "2026-05-02")
    with pytest.raises(RuntimeError):
        BaostockProvider().fetch_daily("002594", "2026-05-01", "2026-05-02")
