from __future__ import annotations

import pandas as pd

from src.regime import (
    category_rotation_from_rows,
    market_regime_summary,
    regime_series,
    rotation_buckets,
)


def prices(closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "trade_date": [f"2026-01-{(i % 28) + 1:02d}" for i in range(len(closes))],
            "open": closes,
            "high": [value * 1.01 for value in closes],
            "low": [value * 0.99 for value in closes],
            "close": closes,
            "volume": [1000 + i for i in range(len(closes))],
        }
    )


def test_market_regime_detects_bull_trend() -> None:
    summary = market_regime_summary(prices([100 + i for i in range(90)]))
    assert summary["trend"] == "bull trend"
    assert "bull trend" in summary["labels"]
    assert summary["ma20"] > summary["ma60"]


def test_market_regime_detects_bear_trend_and_risk_off() -> None:
    summary = market_regime_summary(prices([200 - i for i in range(90)]))
    assert summary["trend"] == "bear trend"
    assert summary["risk"] == "risk-off"
    assert summary["drawdown_60d"] < -0.15


def test_regime_series_adds_indicators() -> None:
    series = regime_series(prices([100 + i for i in range(70)]))
    assert {"ma20", "ma60", "drawdown_60d", "volatility_20d"}.issubset(series.columns)
    assert len(series) == 70


def test_category_rotation_buckets() -> None:
    rows = pd.DataFrame(
        [
            {
                "code": "A",
                "category": "AI",
                "5d_return": 0.03,
                "20d_return": 0.08,
                "60d_return": 0.15,
                "above_ma20": True,
            },
            {
                "code": "B",
                "category": "新能源",
                "5d_return": -0.02,
                "20d_return": 0.04,
                "60d_return": 0.12,
                "above_ma20": True,
            },
            {
                "code": "C",
                "category": "消费",
                "5d_return": 0.04,
                "20d_return": -0.01,
                "60d_return": -0.04,
                "above_ma20": False,
            },
        ]
    )
    rotation = category_rotation_from_rows(rows)
    buckets = rotation_buckets(rotation)
    assert "AI" in buckets["strong"]
    assert "新能源" in buckets["weakening"]
    assert "消费" in buckets["improving"]
