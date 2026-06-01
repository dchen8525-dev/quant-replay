from __future__ import annotations

import pandas as pd

from src import database
from src.research.notebook_export import dataframe_to_csv_bytes, markdown_to_html, text_bytes
from src.research.report_builder import (
    build_factor_report,
    build_markdown_report,
    build_portfolio_report,
    build_strategy_report,
    build_trade_review_report,
)
from src.research.reproducibility import reproducibility_metadata, stable_hash
from src.research.snapshots import compare_snapshots, list_snapshots, save_snapshot


def test_markdown_report_builder() -> None:
    report = build_markdown_report(
        "Test Report",
        {
            "Metrics": {"return": "10%"},
            "Rows": pd.DataFrame([{"code": "002594", "return": 0.1}]),
            "Notes": ["first", "second"],
        },
    )
    assert "# Test Report" in report
    assert "002594" in report
    assert "first" in report


def test_specific_report_builders() -> None:
    df = pd.DataFrame([{"name": "x", "value": 1}])
    assert "Trade Review Report" in build_trade_review_report({}, df, df, df, ["insight"])
    assert "Strategy Backtest Report" in build_strategy_report(df)
    assert "Factor Research Report" in build_factor_report(df)
    assert "Portfolio Report" in build_portfolio_report({"return": 0.1}, df)


def test_exports() -> None:
    markdown = "# Title\n\nhello"
    assert b"Title" in text_bytes(markdown)
    assert "<h1>Title</h1>" in markdown_to_html(markdown)
    csv_bytes = dataframe_to_csv_bytes(pd.DataFrame([{"a": 1}]))
    assert b"a" in csv_bytes


def test_reproducibility_hash_is_stable() -> None:
    payload = {"b": 2, "a": 1}
    assert stable_hash(payload) == stable_hash({"a": 1, "b": 2})
    metadata = reproducibility_metadata("trade", {"x": 1}, {"rows": 2})
    assert metadata["snapshot_hash"]


def test_snapshot_save_and_compare(tmp_path) -> None:
    database.set_db_path(tmp_path / "test.db")
    database.init_db()
    first = save_snapshot("one", "trade", {"a": 1}, "# one")
    second = save_snapshot("two", "trade", {"a": 2}, "# two")
    snapshots = list_snapshots()
    assert len(snapshots) == 2
    comparison = compare_snapshots(first, second)
    assert not comparison["same_hash"]
    database.reset_db_path()
