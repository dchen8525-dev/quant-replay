from __future__ import annotations

from datetime import datetime

import pandas as pd


def build_markdown_report(title: str, sections: dict[str, pd.DataFrame | dict | list | str]) -> str:
    lines = [f"# {title}", "", f"Generated at: {datetime.now().isoformat(timespec='seconds')}", ""]
    for name, content in sections.items():
        lines.extend([f"## {name}", ""])
        if isinstance(content, pd.DataFrame):
            lines.append(_dataframe_to_markdown(content))
        elif isinstance(content, dict):
            for key, value in content.items():
                lines.append(f"- **{key}**: {value}")
        elif isinstance(content, list):
            for item in content:
                lines.append(f"- {item}")
        else:
            lines.append(str(content))
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def build_trade_review_report(
    overall: dict,
    by_tag: pd.DataFrame,
    by_category: pd.DataFrame,
    by_confidence: pd.DataFrame,
    insights: list[str],
) -> str:
    return build_markdown_report(
        "Trade Review Report",
        {
            "Overall": overall,
            "By Tag": by_tag,
            "By Category": by_category,
            "By Confidence": by_confidence,
            "Learning Insights": insights,
        },
    )


def build_strategy_report(experiments: pd.DataFrame) -> str:
    return build_markdown_report("Strategy Backtest Report", {"Experiment History": experiments})


def build_factor_report(factor_summary: pd.DataFrame) -> str:
    return build_markdown_report("Factor Research Report", {"Factor Summary": factor_summary})


def build_portfolio_report(metrics: dict, weights: pd.DataFrame) -> str:
    return build_markdown_report("Portfolio Report", {"Metrics": metrics, "Weights": weights})


def build_monthly_learning_report(sections: dict[str, pd.DataFrame | dict | list | str]) -> str:
    return build_markdown_report("Monthly Learning Report", sections)


def _dataframe_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No data._"
    return df.to_markdown(index=False)
