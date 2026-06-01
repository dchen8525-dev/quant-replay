from __future__ import annotations

import re
from datetime import date, datetime

SH_PREFIXES = ("600", "601", "603", "605", "688")
SZ_PREFIXES = ("000", "001", "002", "003", "300", "301")


def normalize_code(code: str) -> str:
    return re.sub(r"\D", "", str(code or "").strip())[:6]


def validate_stock_code(code: str) -> tuple[bool, str]:
    normalized = normalize_code(code)
    if not re.fullmatch(r"\d{6}", normalized):
        return False, "股票代码必须是 6 位数字。"
    if not normalized.startswith(SH_PREFIXES + SZ_PREFIXES):
        return False, "暂不支持该代码前缀。"
    return True, normalized


def to_akshare_symbol(code: str) -> str:
    valid, value = validate_stock_code(code)
    if not valid:
        raise ValueError(value)
    if value.startswith(SH_PREFIXES):
        return f"sh{value}"
    return f"sz{value}"


def compact_date(value: str | date | datetime) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y%m%d")
    if isinstance(value, date):
        return value.strftime("%Y%m%d")
    text = str(value).strip()
    if re.fullmatch(r"\d{8}", text):
        return text
    return datetime.strptime(text[:10], "%Y-%m-%d").strftime("%Y%m%d")


def iso_date(value: str | date | datetime) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    text = str(value).strip()
    if re.fullmatch(r"\d{8}", text):
        return datetime.strptime(text, "%Y%m%d").strftime("%Y-%m-%d")
    return datetime.strptime(text[:10], "%Y-%m-%d").strftime("%Y-%m-%d")


def today_iso() -> str:
    return date.today().isoformat()
