# QuantReplay

QuantReplay is a local A-share simulated trading replay and quant-learning tool. It records manual simulated buy trades, caches daily price data, replays later market behavior, and reports profit/loss, drawdown, floating loss, and stop-loss outcomes.

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

## Data Providers

The app uses a provider abstraction:

- `AkshareTencentProvider`
- `AkshareEastmoneyProvider`
- `MockProvider`

Tencent is preferred because this environment has known SSL failures when using AKShare's Eastmoney-backed `stock_zh_a_hist()`. Eastmoney remains available as an optional fallback and its failures are caught and logged so the app does not crash.

## Features

- New simulated buy trade
- Historical daily price fetch and SQLite cache
- Trade analysis: final return, profit, max floating profit/loss, max drawdown, holding days
- Stop-loss simulation at 3%, 5%, 8%, and 10%
- Trade history and dashboard summaries
- Watchlist management
- Data diagnostics for provider and cache status

## Limitations

- V1 is local-first and single-user.
- Benchmark comparison is a flat baseline placeholder.
- No real trading, broker login, order execution, tick data, Level2 data, high-frequency trading, or machine learning prediction.

## Roadmap

- Add real benchmark index provider.
- Add provider coverage checks for partial cache ranges.
- Add import/export for trades and watchlist.
- Add richer behavior tags and decision review reports.
