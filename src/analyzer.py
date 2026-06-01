from __future__ import annotations

import pandas as pd


STOP_LOSS_THRESHOLDS = [-0.03, -0.05, -0.08, -0.10]


def analyze_trade(prices: pd.DataFrame, buy_price: float, quantity: int, buy_date: str) -> dict:
    if prices.empty:
        raise ValueError("没有可用于分析的行情数据。")
    if buy_price <= 0:
        raise ValueError("买入价格必须大于 0。")
    if quantity <= 0:
        raise ValueError("数量必须大于 0。")

    df = prices.copy().sort_values("trade_date")
    df = df[df["trade_date"] >= buy_date]
    if df.empty:
        raise ValueError("买入日期之后没有交易数据。")

    actual_start_date = str(df.iloc[0]["trade_date"])
    final_close = float(df.iloc[-1]["close"])
    max_high = float(df["high"].max())
    min_low = float(df["low"].min())
    returns = df["close"] / buy_price - 1
    running_max = df["close"].cummax()
    drawdown = df["close"] / running_max - 1

    result = {
        "actual_start_date": actual_start_date,
        "final_close": final_close,
        "final_return": (final_close - buy_price) / buy_price,
        "final_profit": (final_close - buy_price) * quantity,
        "max_floating_profit": (max_high - buy_price) / buy_price,
        "max_floating_loss": (min_low - buy_price) / buy_price,
        "max_drawdown": float(drawdown.min()),
        "holding_days": int(len(df)),
        "highest_price_after_buy": max_high,
        "lowest_price_after_buy": min_low,
        "initial_cost": buy_price * quantity,
        "final_market_value": final_close * quantity,
        "stop_loss": stop_loss_simulation(df, buy_price),
    }
    result["series"] = df.assign(return_rate=returns.values, drawdown=drawdown.values)
    return result


def stop_loss_simulation(prices: pd.DataFrame, buy_price: float) -> list[dict]:
    rows = []
    for threshold in STOP_LOSS_THRESHOLDS:
        stopped = prices[prices["low"] <= buy_price * (1 + threshold)]
        if stopped.empty:
            rows.append({"threshold": threshold, "triggered": False, "date": None, "price": None})
        else:
            first = stopped.iloc[0]
            rows.append(
                {
                    "threshold": threshold,
                    "triggered": True,
                    "date": str(first["trade_date"]),
                    "price": round(buy_price * (1 + threshold), 3),
                }
            )
    return rows


def analyze_many(trades: pd.DataFrame, price_loader) -> pd.DataFrame:
    rows = []
    for trade in trades.to_dict("records"):
        try:
            prices = price_loader(trade["code"], trade["buy_date"], trade["end_date"])
            analysis = analyze_trade(prices, float(trade["buy_price"]), int(trade["quantity"]), trade["buy_date"])
            rows.append({**trade, **{k: v for k, v in analysis.items() if k not in ("series", "stop_loss")}})
        except Exception:
            rows.append({**trade, "final_return": None, "max_floating_loss": None})
    return pd.DataFrame(rows)
