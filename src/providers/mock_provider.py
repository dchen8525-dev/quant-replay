from __future__ import annotations

import pandas as pd

from src.providers.base import DataProvider
from src.utils import iso_date


class MockProvider(DataProvider):
    name = "mock"

    def fetch_daily(self, code: str, start_date: str, end_date: str) -> pd.DataFrame:
        dates = pd.bdate_range(iso_date(start_date), iso_date(end_date))
        if dates.empty:
            return pd.DataFrame(columns=["trade_date", "open", "high", "low", "close", "volume", "amount"])

        base = 20 + (int(code[-2:]) if str(code).isdigit() else 10) / 10
        rows = []
        for i, day in enumerate(dates):
            close = base * (1 + 0.002 * i) + ((i % 7) - 3) * 0.08
            open_price = close * 0.995
            high = close * 1.015
            low = close * 0.985
            rows.append(
                {
                    "trade_date": day.strftime("%Y-%m-%d"),
                    "open": round(open_price, 2),
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "close": round(close, 2),
                    "volume": 1000000 + i * 1000,
                    "amount": round(close * (1000000 + i * 1000), 2),
                }
            )
        return pd.DataFrame(rows)
