from __future__ import annotations

import pandas as pd


class DataProvider:
    name = "base"

    def fetch_daily(self, code: str, start_date: str, end_date: str) -> pd.DataFrame:
        raise NotImplementedError
