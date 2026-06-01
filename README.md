# QuantReplay

QuantReplay is a local A-share simulated trading replay and quant-learning tool. It records manual simulated buy trades, caches daily price data, replays later market behavior, compares trades with indexes, and reports profit/loss, drawdown, floating loss, stop-loss outcomes, and tag-level review statistics.

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
- Historical daily price fetch and SQLite cache
- Trade analysis: final return, profit, max floating profit/loss, max drawdown, holding days
- Stop-loss simulation at 3%, 5%, 8%, and 10%
- Benchmark comparison and excess return
- Trade tags and tag-level statistics
- Trade history and dashboard summaries
- Watchlist management
- CSV import/export and database backup
- Data diagnostics for provider and cache status

## Screenshots

Screenshots will be added after the UI stabilizes.

## Limitations

- V1 is local-first and single-user.
- No real trading, broker login, order execution, tick data, Level2 data, high-frequency trading, or machine learning prediction.

## Roadmap

- Add benchmark selection persistence per trade.
- Add richer decision review reports.
- Add exchange-calendar-aware cache coverage.
