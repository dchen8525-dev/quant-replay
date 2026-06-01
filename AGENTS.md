# AGENTS.md

## Project Goal

Build an A-share quantitative learning tool for simulated trading and post-trade analysis.

The first version should let the user manually input a simulated buy trade, then analyze whether the trade made money or lost money over a selected period.

Use this stack:

- Python
- pandas
- AKShare for A-share data
- SQLite for local storage
- Streamlit for UI

AKShare provides A-share historical and market data APIs, and Streamlit is suitable for quickly building interactive Python data apps. Use official docs as reference when needed.

## Core Features

### 1. Simulated Buy Trade

User can input:

- stock code
- stock name
- buy date
- buy price
- quantity
- end date
- optional note

Save the trade into SQLite.

### 2. Historical Price Fetching

Fetch A-share historical daily data using AKShare.

Store daily price data locally:

- code
- trade_date
- open
- high
- low
- close
- volume
- amount

Avoid fetching the same data repeatedly if already cached.

### 3. Profit/Loss Analysis

For each simulated trade, calculate:

- initial cost
- final market value
- final profit
- final return rate
- daily floating PnL
- daily return rate
- highest price after buy
- lowest price after buy
- max floating profit
- max floating loss
- max drawdown
- holding days

Formula examples:

```text
profit = (current_close - buy_price) * quantity
return_rate = (current_close - buy_price) / buy_price
max_floating_profit = (max_high_after_buy - buy_price) / buy_price
max_floating_loss = (min_low_after_buy - buy_price) / buy_price