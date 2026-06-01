from __future__ import annotations

import pandas as pd

from src.providers.base import DataProvider
from src.utils import iso_date


class BaostockProvider(DataProvider):
    name = "baostock"

    def fetch_daily(self, code: str, start_date: str, end_date: str) -> pd.DataFrame:
        try:
            import baostock as bs
        except ImportError as exc:
            raise RuntimeError(
                "Baostock is not installed. Install baostock to enable this provider."
            ) from exc

        symbol = _baostock_symbol(code)
        login = bs.login()
        if getattr(login, "error_code", "0") != "0":
            raise RuntimeError(f"Baostock login failed: {getattr(login, 'error_msg', '')}")
        try:
            rs = bs.query_history_k_data_plus(
                symbol,
                "date,open,high,low,close,volume,amount",
                start_date=iso_date(start_date),
                end_date=iso_date(end_date),
                frequency="d",
                adjustflag="2",
            )
            rows = []
            while rs.next():
                rows.append(rs.get_row_data())
            return self._normalize(pd.DataFrame(rows, columns=rs.fields))
        finally:
            bs.logout()

    def _normalize(self, raw: pd.DataFrame) -> pd.DataFrame:
        if raw is None or raw.empty:
            return pd.DataFrame(
                columns=[
                    "trade_date",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "amount",
                ]
            )
        df = raw.rename(columns={"date": "trade_date"}).copy()
        for col in ["open", "high", "low", "close", "volume", "amount"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["trade_date"] = df["trade_date"].map(iso_date)
        return df[["trade_date", "open", "high", "low", "close", "volume", "amount"]].dropna(
            subset=["trade_date", "close"]
        )


def _baostock_symbol(code: str) -> str:
    if code.startswith(("600", "601", "603", "605", "688")):
        return f"sh.{code}"
    return f"sz.{code}"
