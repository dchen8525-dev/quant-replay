from __future__ import annotations

import json
from datetime import datetime

import pandas as pd

from src import database
from src.research.reproducibility import stable_hash


def save_snapshot(name: str, report_type: str, payload: dict, markdown: str) -> int:
    snapshot_hash = stable_hash(
        {"report_type": report_type, "payload": payload, "markdown": markdown}
    )
    return database.execute(
        """
        INSERT INTO research_snapshots
            (name, report_type, payload_json, markdown, snapshot_hash, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            report_type,
            json.dumps(payload, ensure_ascii=False, default=str),
            markdown,
            snapshot_hash,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )


def list_snapshots() -> pd.DataFrame:
    return database.read_df(
        """
        SELECT id, name, report_type, snapshot_hash, created_at
        FROM research_snapshots
        ORDER BY created_at DESC, id DESC
        """
    )


def get_snapshot(snapshot_id: int) -> pd.Series | None:
    df = database.read_df("SELECT * FROM research_snapshots WHERE id = ?", (snapshot_id,))
    if df.empty:
        return None
    return df.iloc[0]


def compare_snapshots(left_id: int, right_id: int) -> dict:
    left = get_snapshot(left_id)
    right = get_snapshot(right_id)
    if left is None or right is None:
        raise ValueError("Snapshot not found.")
    return {
        "left_id": left_id,
        "right_id": right_id,
        "same_hash": left["snapshot_hash"] == right["snapshot_hash"],
        "left_hash": left["snapshot_hash"],
        "right_hash": right["snapshot_hash"],
        "left_created_at": left["created_at"],
        "right_created_at": right["created_at"],
    }
