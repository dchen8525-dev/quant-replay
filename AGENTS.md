这里直接给你可用的 `AGENTS.md` 内容，你复制保存即可。

# AGENTS.md

## Project Name

QuantReplay

---

# Project Goal

Build a local A-share simulated trading replay and quant-learning tool.

The system should allow users to:

* manually input simulated buy trades
* fetch historical A-share price data
* replay later market behavior
* analyze profit/loss
* analyze drawdown
* compare with benchmark/index
* gradually learn quant trading through statistical feedback

This is NOT a real-money trading system.

The focus is:

```text
Quant learning
Trading replay
Behavior analysis
Statistical feedback
```

---

# Core Product Philosophy

The system is essentially:

```text
Trading Journal
+
Simulated Trading Replay
+
Quant Learning System
```

The goal is NOT predicting the future.

The goal IS:

```text
Record decisions
Replay outcomes
Analyze behavior
Discover statistical edge
```

---

# Tech Stack

Use:

* Python 3.12
* Streamlit
* pandas
* SQLite
* AKShare
* plotly

DO NOT use:

* FastAPI
* React
* PostgreSQL
* Redis
* Kafka
* Docker
* Go
* Real broker APIs

Keep V1 lightweight and local-first.

---

# Important Network / Data Source Decision

The user's environment has SSL issues when using:

```python
ak.stock_zh_a_hist()
```

The Eastmoney HTTPS source fails with:

```text
SSL: DECRYPTION_FAILED_OR_BAD_RECORD_MAC
```

But Tencent provider works:

```python
ak.stock_zh_a_hist_tx()
```

Therefore:

## V1 Rules

1. Prefer Tencent provider first.
2. Eastmoney provider should be optional fallback.
3. Eastmoney failures must NEVER crash the app.
4. Build provider abstraction from day one.
5. Future providers:

   * Baostock
   * Tushare

---

# Data Provider Architecture

Implement provider abstraction.

## Base Interface

```python
class DataProvider:
    def fetch_daily(
        self,
        code: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        raise NotImplementedError
```

---

# Providers

Implement:

```text
AkshareTencentProvider
AkshareEastmoneyProvider
MockProvider
```

Optional later:

```text
BaostockProvider
TushareProvider
```

---

# Tencent Provider

Use:

```python
ak.stock_zh_a_hist_tx(
    symbol="sz002594",
    start_date="20260501",
    end_date="20260601",
    adjust="qfq"
)
```

---

# Symbol Conversion Rules

```text
600xxx -> sh
601xxx -> sh
603xxx -> sh
605xxx -> sh
688xxx -> sh

000xxx -> sz
001xxx -> sz
002xxx -> sz
003xxx -> sz
300xxx -> sz
301xxx -> sz
```

---

# Internal Unified Schema

Normalize all providers into:

```python
{
    "trade_date": "",
    "open": 0,
    "high": 0,
    "low": 0,
    "close": 0,
    "volume": 0
}
```

---

# File Structure

```text
quant-replay/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   └── quant_replay.db
└── src/
    ├── __init__.py
    ├── database.py
    ├── data_fetcher.py
    ├── analyzer.py
    ├── charts.py
    ├── utils.py
    ├── models.py
    └── providers/
        ├── __init__.py
        ├── base.py
        ├── akshare_tencent.py
        ├── akshare_eastmoney.py
        └── mock_provider.py
```

---

# Database Schema

Use SQLite.

## stocks

```sql
CREATE TABLE IF NOT EXISTS stocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT,
    industry TEXT,
    created_at TEXT
);
```

---

## daily_prices

```sql
CREATE TABLE IF NOT EXISTS daily_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    trade_date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,
    amount REAL,
    source TEXT,
    adjust TEXT,
    created_at TEXT,
    UNIQUE(code, trade_date, adjust)
);
```

---

## simulated_trades

```sql
CREATE TABLE IF NOT EXISTS simulated_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    name TEXT,
    industry TEXT,
    buy_date TEXT NOT NULL,
    actual_start_date TEXT,
    buy_price REAL NOT NULL,
    quantity INTEGER NOT NULL,
    end_date TEXT NOT NULL,
    reason TEXT,
    confidence INTEGER,
    note TEXT,
    created_at TEXT
);
```

---

## watchlist

```sql
CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT,
    industry TEXT,
    category TEXT,
    priority INTEGER,
    note TEXT,
    created_at TEXT
);
```

---

# Seed Watchlist

Insert these core stocks:

```text
002594 比亚迪
603129 春风动力
300866 安克创新
300896 爱美客
300666 江丰电子
300458 全志科技
601689 拓普集团
002050 三花智控
600309 万华化学
600481 双良节能
002129 TCL中环
002049 紫光国微
300339 润和软件
600095 湘财股份
000725 京东方A
```

---

# Streamlit Pages

Use sidebar navigation:

```text
Dashboard
New Simulated Trade
Trade Analysis
Trade History
Watchlist
Data Diagnostics
```

---

# Dashboard Page

Show:

* total trades
* win rate
* average return
* average max floating loss
* best trade
* worst trade
* industry distribution
* return distribution

---

# New Simulated Trade Page

Input fields:

* stock code
* stock name
* industry
* buy date
* buy price
* quantity
* end date
* buy reason
* confidence (1~5)
* note

After submit:

1. save trade
2. fetch/cache data
3. calculate analysis
4. display result immediately

---

# Trade Analysis Page

Allow selecting existing trade.

Show:

* final return
* final profit
* maximum floating profit
* maximum floating loss
* maximum drawdown
* holding days
* highest price after buy
* lowest price after buy
* stop-loss simulation

---

# Trade History Page

Display table:

```text
code
name
buy_date
buy_price
quantity
end_date
final_return
max_floating_loss
reason
confidence
```

---

# Watchlist Page

Support categories:

```text
新能源
汽车链
AI/半导体
消费成长
周期化工
金融情绪
光伏
机器人/设备
其他
```

Allow:

* add stock
* remove stock
* edit notes
* set priority

---

# Data Diagnostics Page

Very important.

Display:

* Tencent provider status
* Eastmoney provider status
* latest fetched rows
* cache status
* provider error logs

Eastmoney SSL failure must NEVER crash app.

---

# Required Analysis Metrics

## Final Return

```python
(final_close - buy_price) / buy_price
```

---

## Final Profit

```python
(final_close - buy_price) * quantity
```

---

## Maximum Floating Profit

```python
(max_high_after_buy - buy_price) / buy_price
```

---

## Maximum Floating Loss

```python
(min_low_after_buy - buy_price) / buy_price
```

---

## Maximum Drawdown

```python
running_max = close.cummax()
drawdown = close / running_max - 1
max_drawdown = drawdown.min()
```

---

# Stop-Loss Simulation

Simulate:

```text
-3%
-5%
-8%
-10%
```

Example:

```text
This trade ended with a 6.8% gain.

During the holding period,
maximum floating loss reached -3.2%.

If stop-loss threshold was 3%,
the trade would have been stopped out.
```

---

# Charts

Use Plotly.

Required:

1. price line chart
2. return curve
3. drawdown curve
4. buy point marker
5. benchmark comparison

---

# Data Cache Rules

Before remote fetch:

1. check SQLite cache
2. if cache covers range → use cache
3. otherwise fetch missing data
4. normalize
5. save locally

---

# Edge Cases

Handle:

* invalid stock code
* empty data
* non-trading buy date
* suspended stock
* provider failure
* Eastmoney SSL failure
* duplicate rows
* negative price
* zero quantity
* end date before buy date
* future dates

For non-trading buy date:

```text
Keep original buy_date
Use next trading day as actual_start_date
```

---

# requirements.txt

```txt
streamlit
pandas
akshare
plotly
```

Optional:

```txt
baostock
```

---

# README Requirements

README must explain:

* project purpose
* installation
* run command
* provider architecture
* why Tencent provider is preferred
* Eastmoney SSL issue
* roadmap
* limitations

Run command:

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

# Validation Checklist

After implementation verify:

## App

* app starts successfully
* SQLite initializes automatically

## Data

* Tencent provider works
* cache works
* duplicate rows handled

## Trade Flow

* add simulated trade
* fetch data
* calculate metrics
* render charts

## Failure Handling

* Eastmoney SSL failure does not crash app
* invalid stock code handled
* empty data handled

---

# V1 Scope

Focus ONLY on:

```text
Simulated trading
Replay
Profit/loss analysis
Quant learning
```

DO NOT implement:

* real trading
* broker login
* auto order execution
* machine learning prediction
* tick data
* Level2 order book
* high frequency trading
* distributed architecture
* cloud deployment

```
```