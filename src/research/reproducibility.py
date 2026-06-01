from __future__ import annotations

import hashlib
import json


def stable_hash(payload: dict) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def reproducibility_metadata(report_type: str, params: dict, data_counts: dict[str, int]) -> dict:
    payload = {"report_type": report_type, "params": params, "data_counts": data_counts}
    return {
        "report_type": report_type,
        "params": params,
        "data_counts": data_counts,
        "snapshot_hash": stable_hash(payload),
    }
