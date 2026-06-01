from __future__ import annotations

import pandas as pd

from src.portfolio.construction import construct_portfolio
from src.portfolio.metrics import portfolio_metrics


def rebalance_dates(price_map: dict[str, pd.DataFrame], frequency: str = "monthly") -> list[str]:
    dates = sorted(
        set().union(*[set(df["trade_date"]) for df in price_map.values() if not df.empty])
    )
    if not dates:
        return []
    if frequency == "weekly":
        return dates[::5]
    if frequency == "quarterly":
        return dates[::63]
    return dates[::21]


def run_portfolio_backtest(
    price_map: dict[str, pd.DataFrame],
    universe: pd.DataFrame,
    method: str = "equal",
    score_col: str = "score",
    initial_capital: float = 100000.0,
    max_position: float = 0.2,
    max_category_exposure: float = 0.4,
    cash_reserve: float = 0.1,
    frequency: str = "monthly",
    benchmark_prices: pd.DataFrame | None = None,
) -> dict:
    dates = sorted(
        set().union(*[set(df["trade_date"]) for df in price_map.values() if not df.empty])
    )
    if not dates:
        raise ValueError("Portfolio backtest requires price data.")

    rebalance_set = set(rebalance_dates(price_map, frequency))
    weights = construct_portfolio(
        universe,
        method,
        score_col,
        max_position,
        max_category_exposure,
        cash_reserve,
    )
    current_weights = weights
    equity = float(initial_capital)
    rows = []
    total_turnover = 0.0
    previous_weights = pd.Series(dtype=float)

    returns_by_code = _returns_by_code(price_map)
    for index, trade_date in enumerate(dates):
        if trade_date in rebalance_set:
            current_weights = construct_portfolio(
                universe,
                method,
                score_col,
                max_position,
                max_category_exposure,
                cash_reserve,
            )
            new_weights = current_weights.set_index("code")["target_weight"]
            total_turnover += _turnover(previous_weights, new_weights)
            previous_weights = new_weights

        daily_return = 0.0
        for row in current_weights.to_dict("records"):
            code = row["code"]
            daily_return += row["target_weight"] * returns_by_code.get(code, {}).get(
                trade_date, 0.0
            )
        equity *= 1 + daily_return
        rows.append({"trade_date": trade_date, "equity": equity, "daily_return": daily_return})

    equity_curve = pd.DataFrame(rows)
    benchmark_curve = _benchmark_curve(benchmark_prices, initial_capital, equity_curve)
    metrics = portfolio_metrics(equity_curve, total_turnover)
    if not benchmark_curve.empty:
        metrics["benchmark_return"] = float(
            benchmark_curve.iloc[-1]["equity"] / initial_capital - 1
        )
        metrics["excess_return"] = metrics["portfolio_return"] - metrics["benchmark_return"]
    else:
        metrics["benchmark_return"] = 0.0
        metrics["excess_return"] = metrics["portfolio_return"]
    return {
        "weights": weights,
        "equity_curve": equity_curve,
        "benchmark_curve": benchmark_curve,
        "metrics": metrics,
    }


def _returns_by_code(price_map: dict[str, pd.DataFrame]) -> dict[str, dict[str, float]]:
    result = {}
    for code, prices in price_map.items():
        df = prices.copy().sort_values("trade_date")
        df["return"] = df["close"].pct_change().fillna(0.0)
        result[code] = dict(zip(df["trade_date"], df["return"], strict=False))
    return result


def _turnover(previous: pd.Series, current: pd.Series) -> float:
    all_codes = previous.index.union(current.index)
    prev = previous.reindex(all_codes).fillna(0.0)
    curr = current.reindex(all_codes).fillna(0.0)
    return float((curr - prev).abs().sum() / 2)


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
