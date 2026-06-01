from __future__ import annotations

import json
from datetime import datetime

import pandas as pd

from src import database


def save_experiment(
    name: str,
    strategy_name: str,
    params: dict,
    universe: list[str],
    start_date: str,
    end_date: str,
    benchmark: str,
) -> int:
    return database.execute(
        """
        INSERT INTO experiments
            (
                name, strategy_name, params_json, universe_json,
                start_date, end_date, benchmark, created_at
            )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            strategy_name,
            json.dumps(params, ensure_ascii=False),
            json.dumps(universe, ensure_ascii=False),
            start_date,
            end_date,
            benchmark,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )


def save_experiment_result(experiment_id: int, metrics: dict, result: dict | None = None) -> int:
    return database.execute(
        """
        INSERT INTO experiment_results
            (
                experiment_id, total_return, benchmark_return, excess_return,
                max_drawdown, win_rate, trade_count, result_json, created_at
            )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            experiment_id,
            float(metrics.get("total_return", metrics.get("portfolio_return", 0.0))),
            float(metrics.get("benchmark_return", 0.0)),
            float(metrics.get("excess_return", 0.0)),
            float(metrics.get("max_drawdown", 0.0)),
            float(metrics.get("win_rate", 0.0)),
            int(metrics.get("trade_count", 0)),
            json.dumps(result or {}, ensure_ascii=False, default=str),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )


def experiment_history() -> pd.DataFrame:
    return database.read_df(
        """
        SELECT e.*, r.total_return, r.benchmark_return, r.excess_return,
               r.max_drawdown, r.win_rate, r.trade_count
        FROM experiments e
        LEFT JOIN experiment_results r ON r.experiment_id = e.id
        ORDER BY e.created_at DESC, e.id DESC
        """
    )


def anti_overfitting_warnings(
    params: dict,
    metrics: dict,
    train_rows: int | None = None,
    test_rows: int | None = None,
) -> list[str]:
    warnings: list[str] = []
    if len(params) > 4:
        warnings.append("too many parameters")
    if int(metrics.get("trade_count", 0)) < 3:
        warnings.append("too few trades")
    if metrics.get("total_return", 0.0) > 1 and int(metrics.get("trade_count", 0)) < 5:
        warnings.append("very high return with tiny sample")
    if test_rows is not None and test_rows <= 0:
        warnings.append("test period missing")
    if train_rows is not None and train_rows < 20:
        warnings.append("training sample is small")
    return warnings
