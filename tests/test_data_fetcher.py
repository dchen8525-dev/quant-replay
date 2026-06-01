from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest

from src import database
from src.data_fetcher import DataFetchError, fetch_daily_prices


class EmptyProvider:
    name = "empty"

    def fetch_daily(self, code: str, start_date: str, end_date: str) -> pd.DataFrame:
        return pd.DataFrame(
            columns=["trade_date", "open", "high", "low", "close", "volume", "amount"]
        )


class FailingProvider:
    name = "failing"

    def fetch_daily(self, code: str, start_date: str, end_date: str) -> pd.DataFrame:
        raise RuntimeError("boom")


class StaticProvider:
    name = "static"

    def __init__(self) -> None:
        self.calls = 0

    def fetch_daily(self, code: str, start_date: str, end_date: str) -> pd.DataFrame:
        self.calls += 1
        return pd.DataFrame(
            [
                {
                    "trade_date": start_date,
                    "open": 10,
                    "high": 11,
                    "low": 9,
                    "close": 10,
                    "volume": 1,
                    "amount": 10,
                },
                {
                    "trade_date": end_date,
                    "open": 11,
                    "high": 12,
                    "low": 10,
                    "close": 11,
                    "volume": 1,
                    "amount": 11,
                },
            ]
        )


@pytest.fixture(autouse=True)
def temp_db(tmp_path):
    database.set_db_path(tmp_path / "test.db")
    database.init_db()
    yield
    database.reset_db_path()


def test_cache_miss_then_cache_hit() -> None:
    provider = StaticProvider()
    df, source = fetch_daily_prices("002594", "2026-05-01", "2026-05-04", providers=[provider])
    assert source == "cache+static"
    assert len(df) == 2
    assert provider.calls == 1

    df, source = fetch_daily_prices("002594", "2026-05-01", "2026-05-04", providers=[provider])
    assert source == "cache"
    assert len(df) == 2
    assert provider.calls == 1


def test_provider_fallback() -> None:
    df, source = fetch_daily_prices(
        "002594",
        "2026-05-01",
        "2026-05-04",
        providers=[FailingProvider(), StaticProvider()],
    )
    assert not df.empty
    assert "static" in source


def test_provider_failure_and_empty_data() -> None:
    with pytest.raises(DataFetchError):
        fetch_daily_prices(
            "002594", "2026-05-01", "2026-05-04", providers=[FailingProvider(), EmptyProvider()]
        )


def test_invalid_date_range_and_future_date() -> None:
    with pytest.raises(ValueError):
        fetch_daily_prices("002594", "2026-05-04", "2026-05-01", providers=[StaticProvider()])

    future = (date.today() + timedelta(days=1)).isoformat()
    with pytest.raises(ValueError):
        fetch_daily_prices("002594", "2026-05-01", future, providers=[StaticProvider()])
