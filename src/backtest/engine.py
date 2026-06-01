from __future__ import annotations

import pandas as pd

from src.backtest.metrics import annualized_return, max_drawdown, trade_metrics
from src.backtest.models import BacktestResult
from src.backtest.strategies import build_signals


def run_backtest(
    prices: pd.DataFrame,
    strategy_name: str,
    params: dict | None = None,
    initial_capital: float = 100000.0,
    commission_rate: float = 0.0003,
    slippage_rate: float = 0.0005,
    benchmark_prices: pd.DataFrame | None = None,
) -> BacktestResult:
    if prices.empty or len(prices) < 2:
        raise ValueError("Backtest requires at least two price rows.")
    if initial_capital <= 0:
        raise ValueError("Initial capital must be positive.")

    df = prices.copy().sort_values("trade_date").reset_index(drop=True)
    signals = build_signals(strategy_name, df, params or {})
    cash = float(initial_capital)
    quantity = 0
    entry_date: str | None = None
    entry_price = 0.0
    entry_cost = 0.0
    equity_rows = []
    trades = []

    for i, row in df.iterrows():
        close = float(row["close"])
        trade_date = str(row["trade_date"])

        if i > 0:
            signal = int(signals.iloc[i - 1]["signal"])
            execution_price = float(row["open"]) if pd.notna(row["open"]) else close
            if signal == 1 and quantity == 0:
                buy_price = execution_price * (1 + slippage_rate)
                quantity = int(cash / (buy_price * (1 + commission_rate)))
                if quantity > 0:
                    gross = quantity * buy_price
                    commission = gross * commission_rate
                    cash -= gross + commission
                    entry_date = trade_date
                    entry_price = buy_price
                    entry_cost = gross + commission
            elif signal == -1 and quantity > 0:
                sell_price = execution_price * (1 - slippage_rate)
                gross = quantity * sell_price
                commission = gross * commission_rate
                cash += gross - commission
                profit = (
                    cash - initial_capital if entry_cost == 0 else gross - commission - entry_cost
                )
                holding_days = _holding_days(df, entry_date, trade_date)
                trades.append(
                    {
                        "entry_date": entry_date,
                        "entry_price": entry_price,
                        "exit_date": trade_date,
                        "exit_price": sell_price,
                        "quantity": quantity,
                        "profit": profit,
                        "return_rate": profit / entry_cost if entry_cost else 0.0,
                        "holding_days": holding_days,
                        "exit_reason": "signal",
                    }
                )
                quantity = 0
                entry_date = None
                entry_price = 0.0
                entry_cost = 0.0

        equity_rows.append(
            {
                "trade_date": trade_date,
                "cash": cash,
                "position_value": quantity * close,
                "equity": cash + quantity * close,
            }
        )

    if quantity > 0:
        last = df.iloc[-1]
        sell_price = float(last["close"]) * (1 - slippage_rate)
        gross = quantity * sell_price
        commission = gross * commission_rate
        final_cash = cash + gross - commission
        profit = gross - commission - entry_cost
        trade_date = str(last["trade_date"])
        trades.append(
            {
                "entry_date": entry_date,
                "entry_price": entry_price,
                "exit_date": trade_date,
                "exit_price": sell_price,
                "quantity": quantity,
                "profit": profit,
                "return_rate": profit / entry_cost if entry_cost else 0.0,
                "holding_days": _holding_days(df, entry_date, trade_date),
                "exit_reason": "end",
            }
        )
        equity_rows[-1]["cash"] = final_cash
        equity_rows[-1]["position_value"] = 0.0
        equity_rows[-1]["equity"] = final_cash

    equity_curve = pd.DataFrame(equity_rows)
    trades_df = pd.DataFrame(trades)
    benchmark_curve = _benchmark_curve(benchmark_prices, initial_capital, equity_curve)
    total_return = float(equity_curve.iloc[-1]["equity"] / initial_capital - 1)
    benchmark_return = (
        float(benchmark_curve.iloc[-1]["equity"] / initial_capital - 1)
        if not benchmark_curve.empty
        else 0.0
    )
    metrics = {
        "final_equity": float(equity_curve.iloc[-1]["equity"]),
        "total_return": total_return,
        "benchmark_return": benchmark_return,
        "excess_return": total_return - benchmark_return,
        "annualized_return": annualized_return(total_return, len(equity_curve)),
        "max_drawdown": max_drawdown(equity_curve["equity"]),
    }
    metrics.update(trade_metrics(trades_df))
    return BacktestResult(metrics, equity_curve, trades_df, signals, benchmark_curve)


def _holding_days(df: pd.DataFrame, entry_date: str | None, exit_date: str) -> int:
    if entry_date is None:
        return 0
    mask = (df["trade_date"] >= entry_date) & (df["trade_date"] <= exit_date)
    return int(mask.sum())


def _benchmark_curve(
    benchmark_prices: pd.DataFrame | None,
    initial_capital: float,
    equity_curve: pd.DataFrame,
) -> pd.DataFrame:
    if benchmark_prices is None or benchmark_prices.empty:
        return pd.DataFrame(columns=["trade_date", "equity"])
    bench = benchmark_prices.copy().sort_values("trade_date")
    bench = bench[bench["trade_date"].isin(equity_curve["trade_date"])]
    if bench.empty:
        return pd.DataFrame(columns=["trade_date", "equity"])
    base = float(bench.iloc[0]["close"])
    bench["equity"] = initial_capital * bench["close"] / base
    return bench[["trade_date", "equity"]]
