from __future__ import annotations

import pandas as pd

from src.review import by_category, by_confidence, learning_insights, overall_report


def analyzed() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id": 1,
                "code": "002594",
                "name": "A",
                "industry": "新能源",
                "confidence": 5,
                "final_return": 0.1,
                "excess_return": 0.05,
                "max_floating_loss": -0.02,
            },
            {
                "id": 2,
                "code": "600519",
                "name": "B",
                "industry": "消费",
                "confidence": 1,
                "final_return": -0.05,
                "excess_return": -0.08,
                "max_floating_loss": -0.1,
            },
        ]
    )


def test_overall_report() -> None:
    report = overall_report(analyzed())
    assert report["total_trades"] == 2
    assert report["win_rate"] == 0.5
    assert report["best_trade"].startswith("002594")


def test_group_reports() -> None:
    assert len(by_category(analyzed())) == 2
    assert len(by_confidence(analyzed())) == 2


def test_learning_insights() -> None:
    tags = pd.DataFrame([{"trade_id": 1, "tag": "低吸"}, {"trade_id": 2, "tag": "追高"}])
    insights = learning_insights(analyzed(), tags)
    assert any("best-performing tag" in item for item in insights)
