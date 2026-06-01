from __future__ import annotations

from src.strategy_lab.models import StrategySpec

STRATEGIES = {
    "MA Cross": StrategySpec(
        "MA Cross",
        {"ma_short": [5, 10], "ma_long": [20, 30]},
        "Buy when short MA crosses above long MA; sell on reverse cross.",
    ),
    "Breakout": StrategySpec(
        "Breakout",
        {"window": [20, 40], "ma_exit": [10, 20]},
        "Buy breakouts above prior highs; sell below exit MA.",
    ),
    "Mean Reversion": StrategySpec(
        "Mean Reversion",
        {"ma": [20, 30], "threshold": [-0.03, -0.05]},
        "Buy when price is stretched below MA; sell when it returns to MA.",
    ),
    "Strength Rotation": StrategySpec(
        "Strength Rotation",
        {"top_n": [3, 5], "rebalance_days": [5, 20]},
        "Rank candidates by recent strength and rotate into leaders.",
    ),
    "Factor Ranking": StrategySpec(
        "Factor Ranking",
        {"factor": ["momentum_20d", "ma_distance_20d"], "top_n": [3, 5]},
        "Rank candidates by selected factor and hold top names.",
    ),
}


def list_strategies() -> list[str]:
    return list(STRATEGIES)


def get_strategy(name: str) -> StrategySpec:
    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {name}")
    return STRATEGIES[name]


def to_backtest_strategy(name: str) -> str:
    mapping = {
        "MA Cross": "Moving Average Cross",
        "Breakout": "Breakout",
        "Mean Reversion": "Mean Reversion",
        "Strength Rotation": "Moving Average Cross",
        "Factor Ranking": "Breakout",
    }
    return mapping[name]
