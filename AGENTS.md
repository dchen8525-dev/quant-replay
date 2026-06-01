# AGENTS.md

# QuantReplay Development Workflow

Repository:

```text
https://github.com/dchen8525-dev/quant-replay.git
```

QuantReplay is a local A-share simulated trading replay and quant-learning tool.

Current active phase:

```text
PHASE_5
```

Completed phases:

```text
PHASE_1 ✅ COMPLETED
PHASE_2 ✅ COMPLETED
PHASE_3 ✅ COMPLETED
PHASE_4 ✅ COMPLETED
```

Codex must start from:

```text
PHASE_5
```

Do NOT reimplement completed phases unless required for:

* bug fix
* test failure
* dependency issue
* schema compatibility
* security issue

---

# Global Product Rules

QuantReplay is for:

```text
simulated trading
trade replay
quant learning
strategy backtesting
watchlist analysis
behavior review
```

QuantReplay is NOT for:

```text
real-money trading
broker login
automatic order execution
investment advice
high-frequency trading
```

---

# Global Tech Stack

Keep using:

```text
Python 3.12
Streamlit
pandas
SQLite
AKShare
Plotly
pytest
ruff
```

Do NOT migrate to:

```text
FastAPI
React
PostgreSQL
Redis
Kafka
Docker-first architecture
cloud deployment
```

unless a later phase explicitly asks for it.

---

# Data Source Rules

The user's local environment has SSL issues with AKShare Eastmoney source:

```python
ak.stock_zh_a_hist()
```

Error example:

```text
SSL: DECRYPTION_FAILED_OR_BAD_RECORD_MAC
```

Tencent source works:

```python
ak.stock_zh_a_hist_tx()
```

Therefore:

1. Prefer AKShare Tencent provider first.
2. Eastmoney provider must be optional fallback only.
3. Eastmoney failures must never crash the app.
4. Provider errors should be visible in Diagnostics.
5. Keep provider abstraction.

---

# Completed Phase Summary

## PHASE_1 — COMPLETED

Status:

```text
COMPLETED
```

Implemented foundation:

* Streamlit app
* SQLite database
* simulated trade recording
* trade analysis
* provider abstraction
* AKShare Tencent provider
* AKShare Eastmoney provider
* Mock provider
* watchlist
* data diagnostics
* basic charts
* README

Do NOT reimplement.

---

## PHASE_2 — COMPLETED

Status:

```text
COMPLETED
```

Implemented improvements:

* pytest framework
* ruff
* cache improvements
* benchmark comparison
* trade tags
* tag statistics
* import/export
* expanded diagnostics
* page modularization
* README improvements

Do NOT reimplement.

---

# PHASE_3 — COMPLETED

Status:

```text
COMPLETED
```

Main features:

1. Strategy Backtesting
2. Simulated Account
3. Watchlist Strength Ranking
4. Category / Industry Analysis
5. Trade Review Reports
6. Data Quality Improvements
7. UI Polish
8. Tests and README update

---

## PHASE_3.1 Strategy Backtesting

Create:

```text
src/backtest/
├── __init__.py
├── engine.py
├── strategies.py
├── metrics.py
└── models.py
```

Create page:

```text
src/pages/backtest.py
```

Add sidebar entry:

```text
Strategy Backtest
```

### Strategies

Implement beginner-friendly strategies only.

#### Moving Average Cross

```text
Buy when MA_short crosses above MA_long.
Sell when MA_short crosses below MA_long.
```

Default:

```text
MA_short = 5
MA_long = 20
```

#### Breakout

```text
Buy when close > highest high of previous N days.
Sell when close < MA_exit.
```

Default:

```text
N = 20
MA_exit = 10
```

#### Mean Reversion

```text
Buy when close is below MA by X%.
Sell when close returns to MA.
```

Default:

```text
MA = 20
threshold = -5%
```

### Backtest Inputs

UI inputs:

```text
stock code
stock name
start date
end date
initial capital
strategy type
strategy parameters
benchmark
commission rate
slippage rate
```

Defaults:

```text
initial capital = 100000
commission rate = 0.0003
slippage rate = 0.0005
benchmark = 沪深300
```

### Backtest Execution Rules

Rules:

* use daily close price for signal generation
* execute buy/sell at next available trading day's open if possible
* if next open is missing, use next close as fallback
* no short selling
* one position at a time
* all-in position sizing for V1 backtest
* include commission and slippage
* avoid look-ahead bias

Important:

```text
Do NOT use same day's close to generate signal and execute at same close.
```

### Backtest Output

Show metrics:

```text
final equity
total return
benchmark return
excess return
annualized return
max drawdown
win rate
trade count
average profit
average loss
profit factor
holding days
```

Charts:

```text
equity curve
benchmark curve
drawdown curve
buy/sell markers on price chart
```

Trade table:

```text
entry_date
entry_price
exit_date
exit_price
quantity
profit
return_rate
holding_days
exit_reason
```

---

## PHASE_3.2 Simulated Account

Create:

```text
src/account/
├── __init__.py
├── account.py
├── ledger.py
└── metrics.py
```

Create page:

```text
src/pages/account.py
```

Sidebar entry:

```text
Simulated Account
```

### Goal

Allow the user to track multiple simulated trades as one account.

This is different from single-trade replay.

### Account Features

Support:

```text
initial cash
cash balance
open positions
closed trades
account equity curve
total profit/loss
current drawdown
realized PnL
unrealized PnL
```

### SQLite Table

Add:

```sql
CREATE TABLE IF NOT EXISTS account_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_name TEXT NOT NULL,
    trade_date TEXT NOT NULL,
    action TEXT NOT NULL,
    code TEXT NOT NULL,
    name TEXT,
    price REAL NOT NULL,
    quantity INTEGER NOT NULL,
    commission REAL DEFAULT 0,
    note TEXT,
    created_at TEXT
);
```

Actions:

```text
BUY
SELL
```

### Account UI

Allow:

* create default account
* add simulated buy
* add simulated sell
* view current positions
* view transaction ledger
* view account equity curve
* view closed trade statistics

Do not connect to broker APIs.

---

## PHASE_3.3 Watchlist Strength Ranking

Create page:

```text
src/pages/strength.py
```

Sidebar entry:

```text
Strength Ranking
```

### Goal

Rank watchlist stocks by recent performance.

For each watchlist stock calculate:

```text
5-day return
10-day return
20-day return
60-day return
20-day volatility
distance from 20-day high
distance from 60-day high
MA5 / MA20 trend status
volume change if volume is available
```

### Strength Score

Create transparent score:

```text
score =
  30% * 20_day_return_rank
+ 20% * 60_day_return_rank
+ 20% * distance_to_60_day_high_rank
+ 15% * MA_trend_score
+ 15% * inverse_volatility_rank
```

Show table:

```text
rank
code
name
category
5d_return
20d_return
60d_return
volatility
distance_to_high
trend
score
```

Filters:

```text
category
minimum score
show only rising trend
```

---

## PHASE_3.4 Category / Industry Analysis

Use watchlist `category` as industry proxy.

Add dashboard section:

```text
Category Strength
```

Calculate by category:

```text
average 5d return
average 20d return
average 60d return
number of rising stocks
percentage above MA20
best stock
worst stock
```

Show:

```text
category ranking table
category return bar chart
category trend heatmap
```

---

## PHASE_3.5 Trade Review Reports

Create page:

```text
src/pages/review.py
```

Sidebar entry:

```text
Review Report
```

### Report Sections

Overall:

```text
total trades
win rate
average return
median return
average max drawdown
best trade
worst trade
```

By tag:

```text
tag
trade_count
win_rate
average_return
average_excess_return
average_max_floating_loss
```

By category:

```text
category
trade_count
win_rate
average_return
average_excess_return
```

By confidence:

```text
confidence
trade_count
win_rate
average_return
```

### Learning Insights

Generate deterministic template text:

```text
Your best-performing tag is ...
Your worst-performing tag is ...
High-confidence trades are / are not performing better than low-confidence trades.
Your largest losses are concentrated in ...
```

Do not use LLM API.

---

## PHASE_3.6 Data Quality Improvements

Add:

```python
validate_price_df(df: pd.DataFrame) -> list[str]
```

Check:

```text
duplicate dates
missing close
zero or negative prices
non-monotonic dates
empty range
```

Show warnings in Diagnostics.

---

## PHASE_3.7 Tests

Add:

```text
tests/test_backtest_engine.py
tests/test_backtest_strategies.py
tests/test_account.py
tests/test_strength.py
tests/test_review.py
```

Backtest tests:

* no look-ahead execution
* MA cross generates expected trades
* commission reduces final equity
* slippage affects execution price
* max drawdown calculation
* empty price data
* single-row price data

Account tests:

* buy reduces cash
* sell increases cash
* average cost calculation
* realized PnL
* unrealized PnL
* cannot sell more than position
* cannot buy with insufficient cash

Strength tests:

* return calculations
* ranking order
* missing data handling
* category aggregation

---

# PHASE_4 — COMPLETED

Status:

```text
COMPLETED
```

Create:

```text
src/factors/
├── __init__.py
├── engine.py
├── library.py
├── evaluator.py
├── metrics.py
└── models.py
```

Create page:

```text
src/pages/factors.py
```

Sidebar entry:

```text
Factor Research
```

## Factor Library

Implement simple factors:

```text
momentum_5d
momentum_20d
momentum_60d
volatility_20d
volume_ratio_5d
ma_distance_20d
drawdown_from_60d_high
turnover_proxy
```

Do not require financial statement data yet.

## Factor Evaluation

For watchlist stocks:

```text
factor value
next 5d return
next 20d return
rank IC
win rate by factor quantile
average return by factor quantile
```

## Output

Show:

```text
factor ranking table
factor quantile return chart
factor IC summary
best / worst factor
```

## Tests

Add:

```text
tests/test_factors.py
```

Test:

* factor calculations
* missing data
* ranking
* quantile grouping
* IC calculation

---

# PHASE_5 — ACTIVE

Status:

```text
ACTIVE
```

Goal:

```text
Add portfolio construction and risk management.
```

Create:

```text
src/portfolio/
├── __init__.py
├── construction.py
├── risk.py
├── rebalance.py
└── metrics.py
```

Create page:

```text
src/pages/portfolio.py
```

Sidebar entry:

```text
Portfolio Lab
```

## Portfolio Features

Support:

```text
equal weight portfolio
score-weighted portfolio
risk-adjusted weight portfolio
max position limit
category exposure limit
cash reserve
rebalance frequency
```

Default:

```text
max single position = 20%
max category exposure = 40%
cash reserve = 10%
rebalance frequency = monthly
```

## Risk Metrics

Calculate:

```text
portfolio return
annualized return
volatility
max drawdown
Sharpe-like ratio
category exposure
single stock exposure
turnover
```

## Portfolio Backtest

Allow user to:

```text
select watchlist subset
select score source
select rebalance frequency
run portfolio simulation
compare with benchmark
```

## Tests

Add:

```text
tests/test_portfolio.py
```

---

# PHASE_6 — PLANNED

Status:

```text
PLANNED
```

Goal:

```text
Add strategy laboratory with parameter experiments.
```

Create:

```text
src/strategy_lab/
├── __init__.py
├── registry.py
├── experiment.py
├── optimizer.py
├── walk_forward.py
└── models.py
```

Create page:

```text
src/pages/strategy_lab.py
```

Sidebar entry:

```text
Strategy Lab
```

## Features

Support:

```text
strategy registry
parameter grid search
walk-forward testing
train/test split
result comparison
experiment history
```

## Strategies

Register:

```text
MA Cross
Breakout
Mean Reversion
Strength Rotation
Factor Ranking
```

## Experiment Tracking

Add SQLite tables:

```sql
CREATE TABLE IF NOT EXISTS experiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    strategy_name TEXT NOT NULL,
    params_json TEXT,
    universe_json TEXT,
    start_date TEXT,
    end_date TEXT,
    benchmark TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS experiment_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id INTEGER NOT NULL,
    total_return REAL,
    benchmark_return REAL,
    excess_return REAL,
    max_drawdown REAL,
    win_rate REAL,
    trade_count INTEGER,
    result_json TEXT,
    created_at TEXT
);
```

## Anti-overfitting Rules

Show warnings when:

```text
too many parameters
too few trades
very high return with tiny sample
test period missing
```

## Tests

Add:

```text
tests/test_strategy_lab.py
```

---

# PHASE_7 — PLANNED

Status:

```text
PLANNED
```

Goal:

```text
Add research workflow and reproducibility.
```

Create:

```text
src/research/
├── __init__.py
├── notebook_export.py
├── report_builder.py
├── snapshots.py
└── reproducibility.py
```

Create page:

```text
src/pages/research.py
```

Sidebar entry:

```text
Research Reports
```

## Features

Support:

```text
generate markdown research report
export experiment results
export charts
save research snapshot
compare snapshots
```

## Report Types

Generate:

```text
trade review report
strategy backtest report
factor research report
portfolio report
monthly learning report
```

## Output

Allow export as:

```text
Markdown
CSV
HTML
```

Do not implement PDF unless simple and stable.

## Tests

Add:

```text
tests/test_research_reports.py
```

---

# PHASE_8 — PLANNED

Status:

```text
PLANNED
```

Goal:

```text
Improve data robustness and multi-provider support.
```

Create:

```text
src/data_quality/
├── __init__.py
├── calendar.py
├── repair.py
├── provider_compare.py
└── health.py
```

## Provider Expansion

Add optional providers:

```text
BaostockProvider
TushareProvider
```

Rules:

* Baostock is optional and free.
* Tushare requires token and must be optional.
* App must work without Tushare token.

## Provider Comparison

Allow comparing:

```text
Tencent vs Eastmoney
Tencent vs Baostock
```

Compare:

```text
row count
date range
close price differences
missing dates
provider errors
```

## Data Health Page

Add page:

```text
Data Health
```

Show:

```text
provider status
cache coverage
data anomalies
duplicate rows
missing prices
```

---

# PHASE_9 — PLANNED

Status:

```text
PLANNED
```

Goal:

```text
Add market regime and industry rotation analysis.
```

Create:

```text
src/regime/
├── __init__.py
├── market.py
├── category_rotation.py
├── signals.py
└── metrics.py
```

Create page:

```text
src/pages/market_regime.py
```

Sidebar entry:

```text
Market Regime
```

## Market Regime Features

Classify market into:

```text
bull trend
bear trend
sideways
high volatility
low volatility
risk-on
risk-off
```

Use simple rules:

```text
index above MA20 and MA60
index drawdown from 60d high
20d volatility percentile
```

## Industry Rotation

Using watchlist category:

```text
category strength ranking
category trend persistence
category rotation chart
```

Output:

```text
which categories are currently strong
which categories are weakening
which categories are improving
```

---

# PHASE_10 — PLANNED

Status:

```text
PLANNED
```

Goal:

```text
Polish product quality and prepare stable release.
```

## Release Work

Add:

```text
CHANGELOG.md
VERSION
release checklist
sample data
screenshots
better README
```

## UX Improvements

Improve:

```text
Chinese UI labels
metric explanations
empty states
loading states
error messages
chart readability
mobile-ish layout where possible
```

## Stable Release Checklist

Before release:

```bash
pytest
ruff check .
streamlit run app.py
```

Verify:

* no raw tracebacks in normal UI
* existing database migrates safely
* provider failure does not crash
* README is accurate
* screenshots updated
* no secrets committed
* no large cache database committed

---

# Database Migration Rules

Always preserve user data.

Use:

```sql
CREATE TABLE IF NOT EXISTS
```

Before adding a column:

1. inspect existing columns
2. only add if missing

Never drop user tables.

Never delete user trades.

Never delete price cache unless user explicitly requests.

---

# Error Handling Rules

Never expose raw tracebacks in normal UI.

User-facing messages should be clear.

Examples:

```text
股票代码格式错误，请输入 6 位 A股代码，例如 002594。
```

```text
没有获取到该时间段的行情数据。可能原因：股票停牌、日期范围错误、数据源暂时不可用。
```

```text
东方财富数据源在当前网络环境下 SSL 连接失败，已忽略该错误。
```

---

# Testing Rules

Every phase must include tests.

Before finishing a phase, run:

```bash
pytest
ruff check .
```

If tests fail:

1. fix tests or code
2. do not ignore failure
3. document any skipped tests and why

---

# README Rules

After each phase, update README with:

```text
new features
how to use
screenshots placeholder
known limitations
test command
roadmap status
```

---

# Roadmap Status Format

Maintain a roadmap section:

```text
PHASE_1 ✅ COMPLETED
PHASE_2 ✅ COMPLETED
PHASE_3 ✅ COMPLETED
PHASE_4 ✅ COMPLETED
PHASE_5 🔄 ACTIVE
PHASE_6 ⏳ PLANNED
PHASE_7 ⏳ PLANNED
PHASE_8 ⏳ PLANNED
PHASE_9 ⏳ PLANNED
PHASE_10 ⏳ PLANNED
```

When finishing PHASE_4:

1. mark PHASE_4 as COMPLETED
2. mark PHASE_5 as ACTIVE
3. continue only if explicitly requested

---

# Final Rule

Codex should proceed phase by phase.

Do not jump to future phases before completing the active phase.

Current active phase:

```text
PHASE_5
```
