from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StrategySpec:
    name: str
    params: dict[str, list]
    description: str


@dataclass(frozen=True)
class ExperimentConfig:
    name: str
    strategy_name: str
    params: dict
    universe: list[str]
    start_date: str
    end_date: str
    benchmark: str
