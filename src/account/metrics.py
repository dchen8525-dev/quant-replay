from __future__ import annotations

import pandas as pd


def current_positions(transactions: pd.DataFrame) -> pd.DataFrame:
    if transactions.empty:
        return pd.DataFrame(columns=["code", "name", "quantity", "average_cost"])
    rows = []
    for code, group in transactions.groupby("code"):
        quantity = 0
        cost = 0.0
        name = str(group.iloc[-1].get("name", ""))
        for row in group.sort_values(["trade_date", "id"]).to_dict("records"):
            qty = int(row["quantity"])
            price = float(row["price"])
            commission = float(row.get("commission", 0) or 0)
            if row["action"] == "BUY":
                cost += qty * price + commission
                quantity += qty
            elif row["action"] == "SELL":
                if qty > quantity:
                    raise ValueError("Cannot sell more than current position.")
                avg = cost / quantity if quantity else 0.0
                cost -= avg * qty
                quantity -= qty
        if quantity > 0:
            rows.append(
                {
                    "code": code,
                    "name": name,
                    "quantity": quantity,
                    "average_cost": cost / quantity,
                }
            )
    return pd.DataFrame(rows)


def realized_pnl(transactions: pd.DataFrame) -> float:
    pnl = 0.0
    for _, group in transactions.groupby("code"):
        quantity = 0
        cost = 0.0
        for row in group.sort_values(["trade_date", "id"]).to_dict("records"):
            qty = int(row["quantity"])
            price = float(row["price"])
            commission = float(row.get("commission", 0) or 0)
            if row["action"] == "BUY":
                cost += qty * price + commission
                quantity += qty
            elif row["action"] == "SELL":
                if qty > quantity:
                    raise ValueError("Cannot sell more than current position.")
                avg = cost / quantity if quantity else 0.0
                pnl += qty * price - commission - avg * qty
                cost -= avg * qty
                quantity -= qty
    return float(pnl)


def unrealized_pnl(positions: pd.DataFrame, latest_prices: dict[str, float]) -> float:
    if positions.empty:
        return 0.0
    total = 0.0
    for row in positions.to_dict("records"):
        latest = latest_prices.get(row["code"], row["average_cost"])
        total += (latest - row["average_cost"]) * row["quantity"]
    return float(total)
