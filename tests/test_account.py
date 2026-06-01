from __future__ import annotations

import pandas as pd
import pytest

from src.account.account import account_summary, validate_buy, validate_sell
from src.account.metrics import current_positions, realized_pnl, unrealized_pnl


def transactions() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id": 1,
                "trade_date": "2026-05-01",
                "action": "BUY",
                "code": "002594",
                "name": "比亚迪",
                "price": 10,
                "quantity": 100,
                "commission": 1,
            },
            {
                "id": 2,
                "trade_date": "2026-05-02",
                "action": "SELL",
                "code": "002594",
                "name": "比亚迪",
                "price": 12,
                "quantity": 40,
                "commission": 1,
            },
        ]
    )


def test_buy_reduces_cash_and_sell_increases_cash() -> None:
    summary = account_summary(transactions(), initial_cash=10000)
    assert summary["cash_balance"] == pytest.approx(10000 - 1001 + 479)


def test_average_cost_and_positions() -> None:
    positions = current_positions(transactions())
    assert positions.iloc[0]["quantity"] == 60
    assert positions.iloc[0]["average_cost"] == pytest.approx(10.01)


def test_realized_and_unrealized_pnl() -> None:
    positions = current_positions(transactions())
    assert realized_pnl(transactions()) == pytest.approx(78.6)
    assert unrealized_pnl(positions, {"002594": 11}) == pytest.approx(59.4)


def test_cannot_sell_more_than_position() -> None:
    with pytest.raises(ValueError):
        validate_sell(current_positions(transactions()), "002594", 100)


def test_cannot_buy_with_insufficient_cash() -> None:
    with pytest.raises(ValueError):
        validate_buy(100, 10, 20)
