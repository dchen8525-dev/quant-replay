from __future__ import annotations

import os

import pandas as pd

from src.providers.base import DataProvider
from src.utils import compact_date, iso_date


class TushareProvider(DataProvider):
    name = "tushare"

    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.getenv("TUSHARE_TOKEN")

    def fetch_daily(self, code: str, start_date: str, end_date: str) -> pd.DataFrame:
        if not self.token:
            raise RuntimeError(
                "Tushare token is not configured. Set TUSHARE_TOKEN to enable this provider."
            )
        try:
            import tushare as ts
        except ImportError as exc:
            raise RuntimeError(
                "Tushare is not installed. Install tushare to enable this provider."
            ) from exc

        pro = ts.pro_api(self.token)
        raw = pro.daily(
            ts_code=_tushare_symbol(code),
            start_date=compact_date(start_date),
            end_date=compact_date(end_date),
        )
        return self._normalize(raw)

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
        df = raw.rename(columns={"vol": "volume"}).copy()
        df["amount"] = pd.to_numeric(df.get("amount", 0), errors="coerce").fillna(0)
        df["trade_date"] = df["trade_date"].map(iso_date)
        for col in ["open", "high", "low", "close", "volume", "amount"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df[["trade_date", "open", "high", "low", "close", "volume", "amount"]].dropna(
            subset=["trade_date", "close"]
        )


def _tushare_symbol(code: str) -> str:
    suffix = "SH" if code.startswith(("600", "601", "603", "605", "688")) else "SZ"
    return f"{code}.{suffix}"
