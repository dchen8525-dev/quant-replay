from __future__ import annotations

import pandas as pd


def repair_price_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    repaired = df.copy()
    repaired["trade_date"] = repaired["trade_date"].astype(str)
    repaired = repaired.drop_duplicates("trade_date", keep="last")
    for col in ["open", "high", "low", "close", "volume", "amount"]:
        if col in repaired.columns:
            repaired[col] = pd.to_numeric(repaired[col], errors="coerce")
    repaired = repaired.dropna(subset=["trade_date", "close"])
    for col in ["open", "high", "low", "close"]:
        if col in repaired.columns:
            repaired = repaired[repaired[col] > 0]
    return repaired.sort_values("trade_date").reset_index(drop=True)
