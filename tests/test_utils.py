from __future__ import annotations

from src.utils import compact_date, iso_date, to_akshare_symbol, validate_stock_code


def test_valid_a_share_codes() -> None:
    for code in ["002594", "600519", "688981", "300750"]:
        valid, normalized = validate_stock_code(code)
        assert valid
        assert normalized == code


def test_invalid_stock_codes() -> None:
    for code in ["123", "900001", "abc123", ""]:
        valid, _ = validate_stock_code(code)
        assert not valid


def test_symbol_conversion() -> None:
    assert to_akshare_symbol("002594") == "sz002594"
    assert to_akshare_symbol("600519") == "sh600519"
    assert to_akshare_symbol("688981") == "sh688981"
    assert to_akshare_symbol("300750") == "sz300750"


def test_date_normalization() -> None:
    assert iso_date("20260501") == "2026-05-01"
    assert iso_date("2026-05-01") == "2026-05-01"
    assert compact_date("20260501") == "20260501"
    assert compact_date("2026-05-01") == "20260501"
