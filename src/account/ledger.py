from __future__ import annotations

from datetime import datetime

import pandas as pd

from src import database


def add_transaction(
    account_name: str,
    trade_date: str,
    action: str,
    code: str,
    name: str,
    price: float,
    quantity: int,
    commission: float = 0.0,
    note: str = "",
) -> int:
    if action not in {"BUY", "SELL"}:
        raise ValueError("Action must be BUY or SELL.")
    if price <= 0 or quantity <= 0:
        raise ValueError("Price and quantity must be positive.")
    return database.execute(
        """
        INSERT INTO account_transactions
            (
                account_name, trade_date, action, code, name, price,
                quantity, commission, note, created_at
            )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            account_name,
            trade_date,
            action,
            code,
            name,
            float(price),
            int(quantity),
            float(commission),
            note,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )


def get_transactions(account_name: str = "default") -> pd.DataFrame:
    return database.read_df(
        """
        SELECT *
        FROM account_transactions
        WHERE account_name = ?
        ORDER BY trade_date, id
        """,
        (account_name,),
    )
