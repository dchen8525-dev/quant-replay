from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "quant_replay.db"
DB_PATH = DEFAULT_DB_PATH

SEED_WATCHLIST = [
    ("002594", "比亚迪", "新能源"),
    ("603129", "春风动力", "汽车链"),
    ("300866", "安克创新", "消费成长"),
    ("300896", "爱美客", "消费成长"),
    ("300666", "江丰电子", "AI/半导体"),
    ("300458", "全志科技", "AI/半导体"),
    ("601689", "拓普集团", "汽车链"),
    ("002050", "三花智控", "机器人/设备"),
    ("600309", "万华化学", "周期化工"),
    ("600481", "双良节能", "光伏"),
    ("002129", "TCL中环", "光伏"),
    ("002049", "紫光国微", "AI/半导体"),
    ("300339", "润和软件", "AI/半导体"),
    ("600095", "湘财股份", "金融情绪"),
    ("000725", "京东方A", "AI/半导体"),
]


def set_db_path(path: str | Path) -> None:
    global DB_PATH
    DB_PATH = Path(path)


def reset_db_path() -> None:
    global DB_PATH
    DB_PATH = DEFAULT_DB_PATH


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT,
                industry TEXT,
                created_at TEXT
            );

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

            CREATE TABLE IF NOT EXISTS provider_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                code TEXT,
                status TEXT NOT NULL,
                message TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS trade_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id INTEGER NOT NULL,
                tag TEXT NOT NULL,
                created_at TEXT,
                UNIQUE(trade_id, tag)
            );

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

            CREATE TABLE IF NOT EXISTS research_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                report_type TEXT NOT NULL,
                payload_json TEXT,
                markdown TEXT,
                snapshot_hash TEXT,
                created_at TEXT
            );
            """
        )
        now = datetime.now().isoformat(timespec="seconds")
        conn.executemany(
            """
            INSERT OR IGNORE INTO watchlist
                (code, name, industry, category, priority, note, created_at)
            VALUES (?, ?, ?, ?, 3, '', ?)
            """,
            [(code, name, category, category, now) for code, name, category in SEED_WATCHLIST],
        )


def read_df(query: str, params: tuple[Any, ...] = ()) -> pd.DataFrame:
    with connect() as conn:
        return pd.read_sql_query(query, conn, params=params)


def execute(query: str, params: tuple[Any, ...] = ()) -> int:
    with connect() as conn:
        cur = conn.execute(query, params)
        return int(cur.lastrowid or 0)


def save_prices(code: str, prices: pd.DataFrame, source: str, adjust: str = "qfq") -> None:
    if prices.empty:
        return
    now = datetime.now().isoformat(timespec="seconds")
    rows = []
    for row in prices.to_dict("records"):
        rows.append(
            (
                code,
                row["trade_date"],
                float(row["open"]),
                float(row["high"]),
                float(row["low"]),
                float(row["close"]),
                float(row.get("volume", 0) or 0),
                float(row.get("amount", 0) or 0),
                source,
                adjust,
                now,
            )
        )
    with connect() as conn:
        conn.executemany(
            """
            INSERT OR REPLACE INTO daily_prices
                (
                    code, trade_date, open, high, low, close, volume,
                    amount, source, adjust, created_at
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )


def get_prices(code: str, start_date: str, end_date: str, adjust: str = "qfq") -> pd.DataFrame:
    return read_df(
        """
        SELECT trade_date, open, high, low, close, volume, amount, source
        FROM daily_prices
        WHERE code = ? AND adjust = ? AND trade_date BETWEEN ? AND ?
        ORDER BY trade_date
        """,
        (code, adjust, start_date, end_date),
    )


def cache_has_any_data_for_range(
    code: str,
    start_date: str,
    end_date: str,
    adjust: str = "qfq",
) -> bool:
    df = read_df(
        """
        SELECT COUNT(*) AS rows
        FROM daily_prices
        WHERE code = ? AND adjust = ? AND trade_date BETWEEN ? AND ?
        """,
        (code, adjust, start_date, end_date),
    )
    return not df.empty and int(df.loc[0, "rows"] or 0) > 0


def get_cached_range(code: str, adjust: str = "qfq") -> tuple[str | None, str | None]:
    df = read_df(
        """
        SELECT MIN(trade_date) AS min_date, MAX(trade_date) AS max_date, COUNT(*) AS rows
        FROM daily_prices
        WHERE code = ? AND adjust = ?
        """,
        (code, adjust),
    )
    if df.empty or int(df.loc[0, "rows"] or 0) == 0:
        return None, None
    return str(df.loc[0, "min_date"]), str(df.loc[0, "max_date"])


def cache_covers(code: str, start_date: str, end_date: str, adjust: str = "qfq") -> bool:
    min_date, max_date = get_cached_range(code, adjust)
    return bool(min_date and max_date and min_date <= start_date and max_date >= end_date)


def add_trade(values: dict[str, Any]) -> int:
    now = datetime.now().isoformat(timespec="seconds")
    return execute(
        """
        INSERT INTO simulated_trades
            (code, name, industry, buy_date, actual_start_date, buy_price, quantity,
             end_date, reason, confidence, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            values["code"],
            values.get("name", ""),
            values.get("industry", ""),
            values["buy_date"],
            values.get("actual_start_date"),
            values["buy_price"],
            values["quantity"],
            values["end_date"],
            values.get("reason", ""),
            values.get("confidence"),
            values.get("note", ""),
            now,
        ),
    )


def get_trades() -> pd.DataFrame:
    return read_df("SELECT * FROM simulated_trades ORDER BY created_at DESC, id DESC")


def get_trade(trade_id: int) -> pd.Series | None:
    df = read_df("SELECT * FROM simulated_trades WHERE id = ?", (trade_id,))
    if df.empty:
        return None
    return df.iloc[0]


def update_trade_actual_start_date(trade_id: int, actual_start_date: str) -> None:
    execute(
        "UPDATE simulated_trades SET actual_start_date = ? WHERE id = ?",
        (actual_start_date, trade_id),
    )


def add_trade_tags(trade_id: int, tags: list[str]) -> None:
    cleaned = sorted({tag.strip() for tag in tags if tag and tag.strip()})
    if not cleaned:
        return
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO trade_tags (trade_id, tag, created_at) VALUES (?, ?, ?)",
            [(trade_id, tag, now) for tag in cleaned],
        )


def get_trade_tags(trade_id: int) -> list[str]:
    df = read_df("SELECT tag FROM trade_tags WHERE trade_id = ? ORDER BY tag", (trade_id,))
    return [] if df.empty else df["tag"].tolist()


def get_all_trade_tags() -> pd.DataFrame:
    return read_df("SELECT trade_id, tag FROM trade_tags ORDER BY trade_id, tag")


def get_watchlist() -> pd.DataFrame:
    return read_df("SELECT * FROM watchlist ORDER BY priority ASC, code ASC")


def upsert_watchlist(values: dict[str, Any]) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    execute(
        """
        INSERT INTO watchlist (code, name, industry, category, priority, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(code) DO UPDATE SET
            name = excluded.name,
            industry = excluded.industry,
            category = excluded.category,
            priority = excluded.priority,
            note = excluded.note
        """,
        (
            values["code"],
            values.get("name", ""),
            values.get("industry", ""),
            values.get("category", "其他"),
            values.get("priority", 3),
            values.get("note", ""),
            now,
        ),
    )


def delete_watchlist(code: str) -> None:
    execute("DELETE FROM watchlist WHERE code = ?", (code,))


def log_provider(provider: str, code: str, status: str, message: str = "") -> None:
    execute(
        """
        INSERT INTO provider_logs (provider, code, status, message, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (provider, code, status, message[:1000], datetime.now().isoformat(timespec="seconds")),
    )


def provider_logs(limit: int = 20) -> pd.DataFrame:
    return read_df("SELECT * FROM provider_logs ORDER BY id DESC LIMIT ?", (limit,))


def clear_provider_logs() -> None:
    execute("DELETE FROM provider_logs")


def clear_price_cache(code: str | None = None) -> None:
    if code:
        execute("DELETE FROM daily_prices WHERE code = ?", (code,))
    else:
        execute("DELETE FROM daily_prices")


def cache_summary() -> pd.DataFrame:
    return read_df(
        """
        SELECT
            code,
            source,
            adjust,
            COUNT(*) AS rows,
            MIN(trade_date) AS start_date,
            MAX(trade_date) AS end_date,
            MAX(created_at) AS last_created_at
        FROM daily_prices
        GROUP BY code, source, adjust
        ORDER BY MAX(created_at) DESC
        """
    )


def price_cache() -> pd.DataFrame:
    return read_df(
        """
        SELECT code, trade_date, open, high, low, close, volume, amount, source, adjust, created_at
        FROM daily_prices
        ORDER BY code, trade_date
        """
    )


def backup_database(destination: str | Path) -> Path:
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        shutil.copy2(DB_PATH, target)
    return target
