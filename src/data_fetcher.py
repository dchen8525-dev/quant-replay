from __future__ import annotations

from datetime import date

import pandas as pd

from src import database
from src.providers import (
    AkshareEastmoneyProvider,
    AkshareIndexTencentProvider,
    AkshareTencentProvider,
    MockProvider,
)
from src.utils import iso_date, validate_stock_code


class DataFetchError(RuntimeError):
    pass


INVALID_STOCK_CODE_MESSAGE = "股票代码格式错误，请输入 6 位 A股代码，例如 002594。"
NO_PRICE_DATA_MESSAGE = (
    "没有获取到该时间段的行情数据。可能原因：股票停牌、日期范围错误、数据源暂时不可用。"
)
FUTURE_DATE_MESSAGE = "结束日期不能晚于今天。"

BENCHMARKS = {
    "沪深300": "sh000300",
    "中证500": "sh000905",
    "上证指数": "sh000001",
    "深证成指": "sz399001",
    "创业板指": "sz399006",
}


def fetch_daily_prices(
    code: str,
    start_date: str,
    end_date: str,
    allow_mock: bool = False,
    providers: list | None = None,
) -> tuple[pd.DataFrame, str]:
    valid, normalized = validate_stock_code(code)
    if not valid:
        raise ValueError(INVALID_STOCK_CODE_MESSAGE)

    providers = providers or _stock_providers(allow_mock)
    return _fetch_with_cache(normalized, start_date, end_date, providers)


def fetch_benchmark_prices(
    benchmark_name: str,
    start_date: str,
    end_date: str,
    allow_mock: bool = False,
    providers: list | None = None,
) -> tuple[pd.DataFrame, str, str]:
    code = BENCHMARKS[benchmark_name]
    providers = providers or [AkshareIndexTencentProvider()]
    if allow_mock:
        providers.append(MockProvider())
    prices, source = _fetch_with_cache(code, start_date, end_date, providers)
    return prices, source, code


def _stock_providers(allow_mock: bool) -> list:
    providers = [AkshareTencentProvider(), AkshareEastmoneyProvider()]
    if allow_mock:
        providers.append(MockProvider())
    return providers


def _fetch_with_cache(
    code: str,
    start_date: str,
    end_date: str,
    providers: list,
) -> tuple[pd.DataFrame, str]:
    start = iso_date(start_date)
    end = iso_date(end_date)
    if end < start:
        raise ValueError("结束日期不能早于买入日期。")
    if end > date.today().isoformat():
        raise ValueError(FUTURE_DATE_MESSAGE)

    ranges = _missing_ranges(code, start, end)
    if not ranges:
        return database.get_prices(code, start, end), "cache"

    used_sources: list[str] = []
    all_errors: list[str] = []
    for range_start, range_end in ranges:
        source, errors = _fetch_range_from_providers(code, range_start, range_end, providers)
        if source:
            used_sources.append(source)
        else:
            all_errors.extend(errors)

    local = database.get_prices(code, start, end)
    if local.empty:
        raise DataFetchError(_friendly_fetch_error(all_errors))
    source_text = "cache+" + ",".join(sorted(set(used_sources))) if used_sources else "cache"
    return local, source_text


def _missing_ranges(code: str, start: str, end: str) -> list[tuple[str, str]]:
    min_cached, max_cached = database.get_cached_range(code)
    if min_cached is None or max_cached is None:
        return [(start, end)]

    ranges: list[tuple[str, str]] = []
    if start < min_cached:
        ranges.append((start, min(end, min_cached)))
    if end > max_cached:
        ranges.append((max(start, max_cached), end))
    if ranges:
        return ranges
    if not database.cache_has_any_data_for_range(code, start, end):
        return [(start, end)]
    return []


def _fetch_range_from_providers(
    code: str,
    start: str,
    end: str,
    providers: list,
) -> tuple[str | None, list[str]]:
    errors: list[str] = []
    for provider in providers:
        try:
            prices = provider.fetch_daily(code, start, end)
            if prices.empty:
                msg = "empty data"
                database.log_provider(provider.name, code, "empty", msg)
                errors.append(f"{provider.name}: {msg}")
                continue
            prices = _sanitize_prices(prices)
            if prices.empty:
                msg = "empty sanitized data"
                database.log_provider(provider.name, code, "empty", msg)
                errors.append(f"{provider.name}: {msg}")
                continue
            database.save_prices(code, prices, provider.name)
            database.log_provider(provider.name, code, "ok", f"{len(prices)} rows")
            return provider.name, errors
        except Exception as exc:
            message = str(exc)
            database.log_provider(
                provider.name, code, "error", _friendly_provider_message(provider.name, message)
            )
            errors.append(f"{provider.name}: {message}")
            continue
    return None, errors


def _friendly_provider_message(provider_name: str, message: str) -> str:
    if provider_name == "eastmoney" and "SSL" in message.upper():
        return "东方财富数据源在当前网络环境下 SSL 连接失败，已忽略该错误。"
    if provider_name == "tencent":
        return "腾讯数据源失败，已尝试备用数据源。"
    return message


def _friendly_fetch_error(errors: list[str]) -> str:
    if not errors:
        return NO_PRICE_DATA_MESSAGE
    if any("SSL" in err.upper() and "eastmoney" in err for err in errors):
        return "东方财富数据源在当前网络环境下 SSL 连接失败，已忽略该错误。"
    return NO_PRICE_DATA_MESSAGE


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
