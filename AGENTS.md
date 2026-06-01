# AGENTS.md

## Project

QuantReplay

Repository:

```text
https://github.com/dchen8525-dev/quant-replay.git
```

## Current Status

The project already has a working V1 foundation:

* Streamlit app
* SQLite database
* simulated trade flow
* daily A-share data cache
* provider abstraction
* Tencent AKShare provider
* Eastmoney AKShare provider
* Mock provider
* analyzer module
* charts module
* watchlist
* data diagnostics page

Do NOT rewrite the whole project.

This phase should improve stability, correctness, and learning value.

---

# Phase 2 Goal

Turn the current prototype into a more reliable quant-learning replay tool.

Focus on:

1. data correctness
2. test coverage
3. benchmark comparison
4. trade review statistics
5. import/export
6. better UX and error handling

---

# Priority 1: Add Tests

Add a test framework.

Use:

```text
pytest
```

Update `requirements.txt`:

```txt
pytest
```

Create:

```text
tests/
├── test_utils.py
├── test_analyzer.py
├── test_database.py
├── test_data_fetcher.py
└── test_providers.py
```

## Required Tests

### utils tests

Test:

* valid A-share codes
* invalid stock codes
* symbol conversion:

  * `002594 -> sz002594`
  * `600519 -> sh600519`
  * `688981 -> sh688981`
  * `300750 -> sz300750`
* date normalization:

  * `20260501`
  * `2026-05-01`

### analyzer tests

Test:

* final return
* final profit
* max floating profit
* max floating loss
* max drawdown
* stop-loss simulation
* non-trading buy date behavior
* empty price data
* invalid buy price
* invalid quantity

Use deterministic fake price DataFrames.

### database tests

Avoid touching the user's real `data/quant_replay.db`.

Refactor database path so tests can use a temporary SQLite file.

Test:

* init_db
* seed watchlist
* save_prices
* get_prices
* add_trade
* get_trades
* provider_logs
* cache_summary

### data_fetcher tests

Test:

* cache hit
* cache miss
* provider fallback
* provider failure
* empty data
* invalid date range
* future end date

Use MockProvider or monkeypatch providers.

---

# Priority 2: Fix Cache Coverage Logic

Current cache logic is too simple.

Problem:

```text
If cache min_date <= start_date and max_date >= end_date,
the app assumes the full range is covered.
```

This can be wrong if there are gaps inside the range.

Improve `cache_covers`.

Because A-shares have weekends, holidays, and suspensions, do NOT require every calendar day.

Instead implement:

```python
def cache_has_any_data_for_range(code, start_date, end_date, adjust="qfq") -> bool
```

and:

```python
def get_cached_range(code, adjust="qfq") -> tuple[str | None, str | None]
```

Then data fetcher behavior:

1. If no cache, fetch full requested range.
2. If cache exists but does not cover start, fetch missing left side.
3. If cache exists but does not cover end, fetch missing right side.
4. Merge and deduplicate.
5. Return local data from SQLite.

Do not overcomplicate with exchange calendars in this phase.

---

# Priority 3: Real Benchmark Comparison

README currently says benchmark comparison is a placeholder.

Replace placeholder benchmark comparison with real index data.

Support at least:

```text
沪深300
中证500
创业板指
上证指数
深证成指
```

Suggested mapping:

```python
BENCHMARKS = {
    "沪深300": "sh000300",
    "中证500": "sh000905",
    "上证指数": "sh000001",
    "深证成指": "sz399001",
    "创业板指": "sz399006",
}
```

Try AKShare Tencent index data first.

If `stock_zh_a_hist_tx` does not work reliably for indexes, implement a separate index provider using an AKShare index API.

Normalize index data into the same schema:

```text
trade_date
open
high
low
close
volume
amount
source
```

Add database support for benchmark/index prices.

Option A:

Reuse `daily_prices` with code like `sh000300`.

Option B:

Create `index_prices`.

Prefer Option A for simplicity.

## Benchmark Metrics

For each trade:

```text
stock_return
benchmark_return
excess_return = stock_return - benchmark_return
outperformed = excess_return > 0
```

Show in Trade Analysis:

* stock final return
* benchmark final return
* excess return
* whether the trade beat benchmark

Show chart:

* stock return curve
* benchmark return curve

---

# Priority 4: Trade Tags and Review Statistics

The project should become a quant-learning journal, not just a PnL calculator.

Add trade tags.

Examples:

```text
放量突破
缩量回踩
MA20突破
行业强势
财报超预期
题材追高
低吸
趋势跟随
均值回归
情绪交易
```

## Database Change

Add table:

```sql
CREATE TABLE IF NOT EXISTS trade_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id INTEGER NOT NULL,
    tag TEXT NOT NULL,
    created_at TEXT,
    UNIQUE(trade_id, tag)
);
```

Add functions:

```python
add_trade_tags(trade_id: int, tags: list[str]) -> None
get_trade_tags(trade_id: int) -> list[str]
get_all_trade_tags() -> pd.DataFrame
```

## UI Changes

In New Simulated Trade page:

* add multi-select tags
* allow custom tags

In Trade Analysis page:

* show tags

In Dashboard:

Add statistics by tag:

```text
tag
trade_count
win_rate
average_return
average_max_floating_loss
average_excess_return
```

This is very important.

The user should learn:

```text
Which buy reasons/tags are actually working?
```

---

# Priority 5: Import / Export

Add local import/export so the user can back up and analyze data outside the app.

## Export

Add buttons:

* Export trades CSV
* Export watchlist CSV
* Export price cache CSV
* Export full SQLite database backup

## Import

Support:

* import watchlist CSV
* import simulated trades CSV

Do validation before insert.

Required CSV fields for trades:

```text
code
name
industry
buy_date
buy_price
quantity
end_date
reason
confidence
note
```

Optional:

```text
tags
```

Tags can be comma-separated.

---

# Priority 6: Better Error Handling

Improve user-facing errors.

Do not show raw Python tracebacks in normal UI.

Common cases:

## Invalid stock code

Show:

```text
股票代码格式错误，请输入 6 位 A股代码，例如 002594。
```

## No price data

Show:

```text
没有获取到该时间段的行情数据。可能原因：股票停牌、日期范围错误、数据源暂时不可用。
```

## Provider failed

Show:

```text
腾讯数据源失败，已尝试备用数据源。
```

## Eastmoney SSL failure

Show:

```text
东方财富数据源在当前网络环境下 SSL 连接失败，已忽略该错误。
```

## Future date

Show:

```text
结束日期不能晚于今天。
```

---

# Priority 7: Improve Data Diagnostics

Current diagnostics should be expanded.

Add:

## Provider test panel

Allow input:

```text
stock code
start date
end date
```

Test:

* Tencent provider
* Eastmoney provider
* Mock provider

Show:

```text
status
row count
first date
last date
error message
```

## Cache panel

Show:

```text
code
source
adjust
rows
start_date
end_date
last_created_at
```

Add buttons:

* clear cache for selected code
* clear all provider logs
* refresh cache summary

---

# Priority 8: Refactor app.py

`app.py` is already functional but should be split for maintainability.

Create:

```text
src/pages/
├── __init__.py
├── dashboard.py
├── new_trade.py
├── trade_analysis.py
├── trade_history.py
├── watchlist.py
└── diagnostics.py
```

Keep `app.py` small:

```python
def main():
    init_db()
    render_sidebar()
    route_page()
```

Do this carefully.

Do not break behavior.

---

# Priority 9: Code Quality

Add:

```text
ruff
```

Optional but recommended.

Update requirements or dev requirements:

```txt
ruff
pytest
```

Add:

```text
pyproject.toml
```

Recommended config:

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

Run:

```bash
python -m pytest
python -m ruff check .
```

---

# Priority 10: README Update

Update README after changes.

Add:

* screenshots section placeholder
* test command
* architecture diagram in text
* provider fallback explanation
* benchmark comparison explanation
* tags/statistics explanation
* import/export explanation

Commands:

```bash
pip install -r requirements.txt
streamlit run app.py
pytest
```

---

# Do Not Implement Yet

Do NOT implement:

* real trading
* broker login
* automatic order execution
* machine learning prediction
* tick data
* Level2 order book
* high-frequency trading
* distributed architecture
* cloud deployment
* user authentication

Keep the app local-first.

---

# Validation Checklist

Before finishing, verify:

## App

* `streamlit run app.py` starts successfully
* all sidebar pages load
* database initializes automatically

## Data

* Tencent provider fetches `002594` successfully
* Eastmoney failure does not crash app
* cache works after first fetch
* cache summary displays correctly

## Trade Flow

* add simulated trade
* analyze trade
* view trade history
* view dashboard
* stop-loss simulation works

## Benchmark

* benchmark index data loads
* benchmark return is calculated
* excess return is shown
* comparison chart renders

## Tags

* tags can be added to trade
* tags show in analysis
* dashboard shows tag statistics

## Import / Export

* export trades CSV works
* export watchlist CSV works
* import watchlist CSV works
* invalid CSV does not crash app

## Tests

* pytest passes
* analyzer tests cover core formulas
* provider fallback tests pass

---

# Expected Result

After this phase, QuantReplay should become a stable local quant-learning tool where the user can:

```text
record simulated trades
fetch A-share data reliably
replay trade outcomes
compare against benchmarks
analyze behavior by tags
export/import data
trust the calculations through tests
```