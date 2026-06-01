from __future__ import annotations

import pandas as pd

from src.backtest.metrics import annualized_return, max_drawdown


def portfolio_metrics(equity_curve: pd.DataFrame, turnover: float = 0.0) -> dict:
    if equity_curve.empty or len(equity_curve) < 2:
        return {
            "portfolio_return": 0.0,
            "annualized_return": 0.0,
            "volatility": 0.0,
            "max_drawdown": 0.0,
            "sharpe_like": 0.0,
            "turnover": turnover,
        }
    equity = pd.to_numeric(equity_curve["equity"], errors="coerce").dropna()
    returns = equity.pct_change().dropna()
    total_return = float(equity.iloc[-1] / equity.iloc[0] - 1)
    volatility = float(returns.std() * (252**0.5)) if not returns.empty else 0.0
    ann = annualized_return(total_return, len(equity))
    return {
        "portfolio_return": total_return,
        "annualized_return": ann,
        "volatility": volatility,
        "max_drawdown": max_drawdown(equity),
        "sharpe_like": ann / volatility if volatility > 0 else 0.0,
        "turnover": float(turnover),
    }
