# QuantReplay

QuantReplay is a local A-share simulated trading replay and quant-learning tool. It records manual simulated buy trades, caches daily price data, replays later market behavior, runs beginner strategy backtests, tracks a simulated account, ranks watchlist strength, compares trades with indexes, and reports profit/loss, drawdown, floating loss, stop-loss outcomes, and review statistics.

It is not a real-money trading system and does not connect to broker APIs.

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

The SQLite database is created automatically at `data/quant_replay.db`.

## Test

```bash
pytest
python -m ruff check .
```

## Architecture

```text
app.py
  -> src/pages/*              Streamlit page rendering
  -> src/data_fetcher.py      cache-aware provider orchestration
  -> src/providers/*          Tencent, Eastmoney, index, mock providers
  -> src/database.py          SQLite persistence, tags, logs, cache
  -> src/backtest/*           beginner strategy backtesting
  -> src/account/*            simulated account ledger and metrics
  -> src/strength.py          watchlist and category strength ranking
  -> src/review.py            deterministic trade review reports
  -> src/factors/*            factor library, ranking, IC, quantile evaluation
  -> src/portfolio/*          portfolio construction, exposure, rebalance, risk metrics
  -> src/strategy_lab/*       strategy registry, parameter grid, walk-forward, experiment history
  -> src/analyzer.py          PnL, drawdown, stop-loss, benchmark, tag stats
  -> src/charts.py            Plotly charts
```

## Data Providers

The app uses a provider abstraction:

- `AkshareTencentProvider`
- `AkshareEastmoneyProvider`
- `AkshareIndexTencentProvider`
- `MockProvider`

Tencent is preferred because this environment has known SSL failures when using AKShare's Eastmoney-backed `stock_zh_a_hist()`. Eastmoney remains available as an optional fallback and its failures are caught and logged so the app does not crash. The fetcher checks the local SQLite cache first, fetches missing left/right ranges when the requested range extends beyond cached data, then merges and deduplicates rows in SQLite.

## Benchmark Comparison

Trade Analysis supports real benchmark comparison for:

- 沪深300
- 中证500
- 上证指数
- 深证成指
- 创业板指

Benchmark data is stored in the same `daily_prices` table using index codes like `sh000300`. The app reports stock return, benchmark return, excess return, and whether the trade outperformed.

## Tags And Review Statistics

Trades can be tagged with common setup labels such as `放量突破`, `低吸`, `趋势跟随`, or custom comma-separated tags. Dashboard aggregates performance by tag so the user can see which trade patterns are working statistically.

## Import / Export

The app supports local backup workflows:

- export trades CSV
- import simulated trades CSV
- export watchlist CSV
- import watchlist CSV
- export price cache CSV
- export full SQLite database backup

## Features

- New simulated buy trade
- Strategy backtesting: moving average cross, breakout, mean reversion
- Simulated account ledger with cash, positions, realized/unrealized PnL
- Watchlist strength ranking and category strength analysis
- Review reports by tag, category, and confidence
- Factor research: simple technical factors, next-return evaluation, rank IC, quantile returns
- Portfolio Lab: equal weight, score-weighted, risk-adjusted portfolios, exposure limits, rebalance simulation
- Strategy Lab: strategy registry, parameter grid search, walk-forward testing, experiment history
- Historical daily price fetch and SQLite cache
- Trade analysis: final return, profit, max floating profit/loss, max drawdown, holding days
- Stop-loss simulation at 3%, 5%, 8%, and 10%
- Benchmark comparison and excess return
- Trade tags and tag-level statistics
- Trade history and dashboard summaries
- Watchlist management
- CSV import/export and database backup
- Data diagnostics for provider and cache status
- Price data quality checks for duplicate dates, missing close, invalid prices, date ordering, and empty ranges

## Backtesting

The Strategy Backtest page uses daily close prices to generate signals and executes trades at the next available trading day's open. This avoids using the same day's close for both signal generation and execution. V1 backtests are long-only, one position at a time, all-in sizing, and include commission and slippage.

Supported beginner strategies:

- Moving Average Cross
- Breakout
- Mean Reversion

## Simulated Account

The Simulated Account page tracks multiple simulated BUY/SELL transactions as one account. It reports cash balance, open positions, account equity, realized PnL, and unrealized PnL. It does not connect to broker APIs.

## Strength Ranking

The Strength Ranking page calculates recent return, volatility, distance from highs, MA trend status, and a transparent 0-100 score for watchlist stocks. Dashboard also shows category strength based on watchlist category.

## Factor Research

The Factor Research page evaluates simple technical factors for watchlist stocks:

- momentum_5d, momentum_20d, momentum_60d
- volatility_20d
- volume_ratio_5d
- ma_distance_20d
- drawdown_from_60d_high
- turnover_proxy

It reports factor ranking, next 5d/20d returns, rank IC, win rate by factor quantile, and average return by quantile. It uses cached/local price data through the same provider abstraction and does not require financial statement data.

## Portfolio Lab

The Portfolio Lab page builds simple watchlist portfolios using:

- equal weight
- score-weighted allocation
- risk-adjusted allocation

It supports max single-position limits, category exposure limits, cash reserve, weekly/monthly/quarterly rebalancing, benchmark comparison, turnover, volatility, max drawdown, Sharpe-like ratio, category exposure, and single-stock exposure.

## Strategy Lab

The Strategy Lab page supports beginner strategy experiments:

- MA Cross
- Breakout
- Mean Reversion
- Strength Rotation
- Factor Ranking

It runs parameter grid search, train/test walk-forward checks, stores experiment history in SQLite, and shows anti-overfitting warnings for too many parameters, too few trades, very high returns with tiny samples, or missing test periods.

## Screenshots

Screenshots will be added after the UI stabilizes.

## Limitations

- V1 is local-first and single-user.
- No real trading, broker login, order execution, tick data, Level2 data, high-frequency trading, or machine learning prediction.

## Roadmap

```text
PHASE_1 ✅ COMPLETED
PHASE_2 ✅ COMPLETED
PHASE_3 ✅ COMPLETED
PHASE_4 ✅ COMPLETED
PHASE_5 ✅ COMPLETED
PHASE_6 ✅ COMPLETED
PHASE_7 🔄 ACTIVE
PHASE_8 ⏳ PLANNED
PHASE_9 ⏳ PLANNED
PHASE_10 ⏳ PLANNED
```

Next active phase: portfolio construction and risk management.
