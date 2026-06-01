from __future__ import annotations

import pandas as pd

from src import database


def test_database_flow(tmp_path) -> None:
    database.set_db_path(tmp_path / "test.db")
    database.init_db()

    assert len(database.get_watchlist()) == 15

    prices = pd.DataFrame(
        [
            {
                "trade_date": "2026-05-01",
                "open": 10,
                "high": 11,
                "low": 9,
                "close": 10,
                "volume": 1,
                "amount": 10,
            },
            {
                "trade_date": "2026-05-04",
                "open": 10,
                "high": 12,
                "low": 10,
                "close": 11,
                "volume": 2,
                "amount": 22,
            },
        ]
    )
    database.save_prices("002594", prices, "mock")
    cached = database.get_prices("002594", "2026-05-01", "2026-05-04")
    assert len(cached) == 2
    assert database.cache_has_any_data_for_range("002594", "2026-05-01", "2026-05-04")
    assert database.get_cached_range("002594") == ("2026-05-01", "2026-05-04")

    trade_id = database.add_trade(
        {
            "code": "002594",
            "name": "比亚迪",
            "industry": "新能源",
            "buy_date": "2026-05-01",
            "buy_price": 10,
            "quantity": 100,
            "end_date": "2026-05-04",
            "reason": "test",
            "confidence": 3,
            "note": "",
        }
    )
    database.add_trade_tags(trade_id, ["低吸", "低吸", "趋势跟随"])
    assert set(database.get_trade_tags(trade_id)) == {"低吸", "趋势跟随"}
    assert len(database.get_all_trade_tags()) == 2
    assert len(database.get_trades()) == 1

    database.log_provider("mock", "002594", "ok", "2 rows")
    assert len(database.provider_logs()) == 1
    assert len(database.cache_summary()) == 1

    database.reset_db_path()
