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


def compare_with_benchmark(stock_series: pd.DataFrame, benchmark_prices: pd.DataFrame) -> dict:
    if stock_series.empty or benchmark_prices.empty:
        raise ValueError("没有可用于基准比较的数据。")

    stock = stock_series[["trade_date", "return_rate"]].rename(
        columns={"return_rate": "stock_return"}
    )
    bench = benchmark_prices.copy().sort_values("trade_date")
    bench = bench[bench["trade_date"].isin(stock["trade_date"])]
    if bench.empty:
        raise ValueError("基准数据与个股持有期没有重合交易日。")
    base_close = float(bench.iloc[0]["close"])
    bench = bench.assign(benchmark_return=bench["close"] / base_close - 1)
    merged = stock.merge(bench[["trade_date", "benchmark_return"]], on="trade_date", how="inner")
    if merged.empty:
        raise ValueError("基准数据与个股持有期没有重合交易日。")

    stock_final = float(merged.iloc[-1]["stock_return"])
    benchmark_final = float(merged.iloc[-1]["benchmark_return"])
    excess = stock_final - benchmark_final
    return {
        "stock_return": stock_final,
        "benchmark_return": benchmark_final,
        "excess_return": excess,
        "outperformed": excess > 0,
        "series": merged,
    }


def analyze_many(trades: pd.DataFrame, price_loader, benchmark_loader=None) -> pd.DataFrame:
    rows = []
    for trade in trades.to_dict("records"):
        try:
            prices = price_loader(trade["code"], trade["buy_date"], trade["end_date"])
            analysis = analyze_trade(
                prices, float(trade["buy_price"]), int(trade["quantity"]), trade["buy_date"]
            )
            result = {
                **trade,
                **{k: v for k, v in analysis.items() if k not in ("series", "stop_loss")},
            }
            if benchmark_loader:
                benchmark = benchmark_loader(trade["buy_date"], trade["end_date"])
                comparison = compare_with_benchmark(analysis["series"], benchmark)
                result.update({k: v for k, v in comparison.items() if k != "series"})
            rows.append(result)
        except Exception:
            rows.append(
                {
                    **trade,
                    "final_return": None,
                    "max_floating_loss": None,
                    "excess_return": None,
                }
            )
    return pd.DataFrame(rows)


def tag_statistics(analyzed_trades: pd.DataFrame, tags: pd.DataFrame) -> pd.DataFrame:
    if analyzed_trades.empty or tags.empty:
        return pd.DataFrame(
            columns=[
                "tag",
                "trade_count",
                "win_rate",
                "average_return",
                "average_max_floating_loss",
                "average_excess_return",
            ]
        )
    merged = tags.merge(analyzed_trades, left_on="trade_id", right_on="id", how="inner")
    if merged.empty:
        return pd.DataFrame()
    return (
        merged.groupby("tag")
        .agg(
            trade_count=("id", "count"),
            win_rate=(
                "final_return",
                lambda s: (s.dropna() > 0).mean() if not s.dropna().empty else None,
            ),
            average_return=("final_return", "mean"),
            average_max_floating_loss=("max_floating_loss", "mean"),
            average_excess_return=("excess_return", "mean"),
        )
        .reset_index()
        .sort_values(["trade_count", "average_return"], ascending=[False, False])
    )
