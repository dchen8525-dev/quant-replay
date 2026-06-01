from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SimulatedTrade:
    code: str
    name: str
    industry: str
    buy_date: str
    buy_price: float
    quantity: int
    end_date: str
    reason: str = ""
    confidence: int | None = None
    note: str = ""
    actual_start_date: str | None = None
