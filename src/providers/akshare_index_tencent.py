from __future__ import annotations

import pandas as pd

from src.providers.base import DataProvider
from src.utils import compact_date, iso_date


class AkshareIndexTencentProvider(DataProvider):
    name = "tencent_index"

    def fetch_daily(self, code: str, start_date: str, end_date: str) -> pd.DataFrame:
        import akshare as ak

        raw = ak.stock_zh_index_daily_tx(
            symbol=code,
            start_date=compact_date(start_date),
            end_date=compact_date(end_date),
        )
        return self._normalize(raw)

    def _normalize(self, raw: pd.DataFrame) -> pd.DataFrame:
        if raw is None or raw.empty:
            return pd.DataFrame(
                columns=["trade_date", "open", "high", "low", "close", "volume", "amount"]
            )

        df = raw.copy()
        df = df.rename(
            columns={
                "date": "trade_date",
                "日期": "trade_date",
                "open": "open",
                "开盘": "open",
                "high": "high",
                "最高": "high",
                "low": "low",
                "最低": "low",
                "close": "close",
                "收盘": "close",
                "volume": "volume",
                "成交量": "volume",
                "amount": "amount",
                "成交额": "amount",
            }
        )
        columns = ["trade_date", "open", "high", "low", "close", "volume", "amount"]
        for col in columns:
            if col not in df.columns:
                df[col] = 0.0 if col != "trade_date" else ""
        df = df[columns]
        df["trade_date"] = df["trade_date"].map(iso_date)
        for col in ["open", "high", "low", "close", "volume", "amount"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df.dropna(subset=["trade_date", "open", "high", "low", "close"]).sort_values(
            "trade_date"
        )
