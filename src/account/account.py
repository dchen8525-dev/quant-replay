from __future__ import annotations

import pandas as pd

from src.account.metrics import current_positions, realized_pnl, unrealized_pnl


def validate_buy(cash: float, price: float, quantity: int, commission: float = 0.0) -> None:
    if price * quantity + commission > cash:
        raise ValueError("Cannot buy with insufficient cash.")


def validate_sell(positions: pd.DataFrame, code: str, quantity: int) -> None:
    current = positions[positions["code"] == code]
    held = 0 if current.empty else int(current.iloc[0]["quantity"])
    if quantity > held:
        raise ValueError("Cannot sell more than current position.")


def account_summary(
    transactions: pd.DataFrame,
    initial_cash: float = 100000.0,
    latest_prices: dict[str, float] | None = None,
) -> dict:
    latest_prices = latest_prices or {}
    cash = float(initial_cash)
    if not transactions.empty:
        for row in transactions.to_dict("records"):
            amount = float(row["price"]) * int(row["quantity"])
            commission = float(row.get("commission", 0) or 0)
            if row["action"] == "BUY":
                cash -= amount + commission
            else:
                cash += amount - commission
    positions = current_positions(transactions)
    realized = realized_pnl(transactions)
    unrealized = unrealized_pnl(positions, latest_prices)
    equity = cash + sum(
        latest_prices.get(row["code"], row["average_cost"]) * row["quantity"]
        for row in positions.to_dict("records")
    )
    return {
        "initial_cash": initial_cash,
        "cash_balance": cash,
        "positions": positions,
        "realized_pnl": realized,
        "unrealized_pnl": unrealized,
        "total_profit_loss": realized + unrealized,
        "equity": float(equity),
    }


def equity_curve(transactions: pd.DataFrame, initial_cash: float = 100000.0) -> pd.DataFrame:
    if transactions.empty:
        return pd.DataFrame([{"trade_date": "", "equity": initial_cash, "cash": initial_cash}])
    rows = []
    cash = float(initial_cash)
    position_cost = 0.0
    for row in transactions.sort_values(["trade_date", "id"]).to_dict("records"):
        amount = float(row["price"]) * int(row["quantity"])
        commission = float(row.get("commission", 0) or 0)
        if row["action"] == "BUY":
            cash -= amount + commission
            position_cost += amount + commission
        else:
            cash += amount - commission
            position_cost = max(0.0, position_cost - amount)
        rows.append(
            {
                "trade_date": row["trade_date"],
                "cash": cash,
                "position_cost": position_cost,
                "equity": cash + position_cost,
            }
        )
    return pd.DataFrame(rows)
