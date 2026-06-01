from __future__ import annotations

from datetime import date

import pandas as pd

from src import database
from src.providers import AkshareEastmoneyProvider, AkshareTencentProvider, MockProvider
from src.utils import iso_date, validate_stock_code


class DataFetchError(RuntimeError):
    pass


def fetch_daily_prices(
    code: str,
    start_date: str,
    end_date: str,
    allow_mock: bool = False,
) -> tuple[pd.DataFrame, str]:
    valid, normalized = validate_stock_code(code)
    if not valid:
        raise ValueError(normalized)

    start = iso_date(start_date)
    end = iso_date(end_date)
    if end < start:
        raise ValueError("结束日期不能早于买入日期。")
    if end > date.today().isoformat():
        raise ValueError("结束日期不能晚于今天。")

    if database.cache_covers(normalized, start, end):
        return database.get_prices(normalized, start, end), "cache"

    providers = [AkshareTencentProvider(), AkshareEastmoneyProvider()]
    if allow_mock:
        providers.append(MockProvider())

    errors: list[str] = []
    for provider in providers:
        try:
            prices = provider.fetch_daily(normalized, start, end)
            if prices.empty:
                msg = "empty data"
                database.log_provider(provider.name, normalized, "empty", msg)
                errors.append(f"{provider.name}: {msg}")
                continue
            prices = _sanitize_prices(prices)
            database.save_prices(normalized, prices, provider.name)
            database.log_provider(provider.name, normalized, "ok", f"{len(prices)} rows")
            return database.get_prices(normalized, start, end), provider.name
        except Exception as exc:
            message = str(exc)
            database.log_provider(provider.name, normalized, "error", message)
            errors.append(f"{provider.name}: {message}")
            continue

    raise DataFetchError("; ".join(errors) or "所有数据源均未返回数据。")


def _sanitize_prices(prices: pd.DataFrame) -> pd.DataFrame:
    df = prices.copy()
    df["trade_date"] = df["trade_date"].map(iso_date)
    for col in ["open", "high", "low", "close", "volume", "amount"]:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["trade_date", "open", "high", "low", "close"])
    df = df[(df["open"] > 0) & (df["high"] > 0) & (df["low"] > 0) & (df["close"] > 0)]
    return df.drop_duplicates("trade_date").sort_values("trade_date")
