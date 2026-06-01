from __future__ import annotations

import pandas as pd

from src.analyzer import tag_statistics


def overall_report(analyzed: pd.DataFrame) -> dict:
    valid = (
        analyzed.dropna(subset=["final_return"]) if "final_return" in analyzed else pd.DataFrame()
    )
    if valid.empty:
        return {
            "total_trades": len(analyzed),
            "win_rate": 0.0,
            "average_return": 0.0,
            "median_return": 0.0,
            "average_max_drawdown": 0.0,
            "best_trade": "",
            "worst_trade": "",
        }
    best = valid.loc[valid["final_return"].idxmax()]
    worst = valid.loc[valid["final_return"].idxmin()]
    return {
        "total_trades": len(analyzed),
        "win_rate": float((valid["final_return"] > 0).mean()),
        "average_return": float(valid["final_return"].mean()),
        "median_return": float(valid["final_return"].median()),
        "average_max_drawdown": float(valid.get("max_drawdown", pd.Series([0])).mean()),
        "best_trade": f"{best['code']} {best.get('name', '')}",
        "worst_trade": f"{worst['code']} {worst.get('name', '')}",
    }


def by_category(analyzed: pd.DataFrame) -> pd.DataFrame:
    if analyzed.empty or "industry" not in analyzed.columns:
        return pd.DataFrame()
    return (
        analyzed.groupby("industry", dropna=False)
        .agg(
            trade_count=("id", "count"),
            win_rate=(
                "final_return",
                lambda s: float((s.dropna() > 0).mean()) if not s.dropna().empty else 0.0,
            ),
            average_return=("final_return", "mean"),
            average_excess_return=("excess_return", "mean"),
        )
        .reset_index()
        .rename(columns={"industry": "category"})
    )


def by_confidence(analyzed: pd.DataFrame) -> pd.DataFrame:
    if analyzed.empty or "confidence" not in analyzed.columns:
        return pd.DataFrame()
    return (
        analyzed.groupby("confidence", dropna=False)
        .agg(
            trade_count=("id", "count"),
            win_rate=(
                "final_return",
                lambda s: float((s.dropna() > 0).mean()) if not s.dropna().empty else 0.0,
            ),
            average_return=("final_return", "mean"),
        )
        .reset_index()
    )


def learning_insights(analyzed: pd.DataFrame, tags: pd.DataFrame) -> list[str]:
    insights: list[str] = []
    tag_stats = tag_statistics(analyzed, tags)
    if not tag_stats.empty:
        best = tag_stats.sort_values("average_return", ascending=False).iloc[0]
        worst = tag_stats.sort_values("average_return", ascending=True).iloc[0]
        insights.append(f"Your best-performing tag is {best['tag']}.")
        insights.append(f"Your worst-performing tag is {worst['tag']}.")
    confidence = by_confidence(analyzed)
    if len(confidence.dropna(subset=["average_return"])) >= 2:
        high = confidence.sort_values("confidence").tail(1).iloc[0]
        low = confidence.sort_values("confidence").head(1).iloc[0]
        verdict = "are" if high["average_return"] > low["average_return"] else "are not"
        insights.append(
            f"High-confidence trades {verdict} performing better than low-confidence trades."
        )
    category = by_category(analyzed)
    if not category.empty and "average_return" in category:
        worst_category = category.sort_values("average_return").iloc[0]
        insights.append(f"Your largest losses are concentrated in {worst_category['category']}.")
    return insights
