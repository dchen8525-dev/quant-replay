from __future__ import annotations

import pandas as pd
import streamlit as st

from src import database
from src.analyzer import analyze_many, tag_statistics
from src.research.notebook_export import dataframe_to_csv_bytes, markdown_to_html, text_bytes
from src.research.report_builder import (
    build_factor_report,
    build_markdown_report,
    build_monthly_learning_report,
    build_strategy_report,
    build_trade_review_report,
)
from src.research.reproducibility import reproducibility_metadata
from src.research.snapshots import compare_snapshots, list_snapshots, save_snapshot
from src.review import by_category, by_confidence, learning_insights, overall_report
from src.strategy_lab.experiment import experiment_history


def research_page() -> None:
    report_type = st.selectbox(
        "报告类型",
        [
            "trade review report",
            "strategy backtest report",
            "factor research report",
            "portfolio report",
            "monthly learning report",
        ],
    )
    snapshot_name = st.text_input("快照名称", value=report_type)
    markdown, export_df, payload = _build_report(report_type)

    st.subheader("Markdown Preview")
    st.code(markdown, language="markdown")
    cols = st.columns(4)
    cols[0].download_button(
        "Export Markdown",
        text_bytes(markdown),
        "research_report.md",
        "text/markdown",
    )
    cols[1].download_button(
        "Export HTML",
        text_bytes(markdown_to_html(markdown)),
        "research_report.html",
        "text/html",
    )
    cols[2].download_button(
        "Export CSV",
        dataframe_to_csv_bytes(export_df),
        "research_data.csv",
        "text/csv",
    )
    if cols[3].button("Save Snapshot"):
        snapshot_id = save_snapshot(snapshot_name, report_type, payload, markdown)
        st.success(f"已保存研究快照 #{snapshot_id}")

    st.subheader("Research Snapshots")
    snapshots = list_snapshots()
    st.dataframe(snapshots, use_container_width=True, hide_index=True)
    if len(snapshots) >= 2:
        ids = snapshots["id"].tolist()
        left, right = st.columns(2)
        left_id = left.selectbox("左侧快照", ids, index=0)
        right_id = right.selectbox("右侧快照", ids, index=1)
        if st.button("Compare Snapshots"):
            st.json(compare_snapshots(int(left_id), int(right_id)))


def _build_report(report_type: str) -> tuple[str, pd.DataFrame, dict]:
    trades = database.get_trades()
    analyzed = analyze_many(trades, lambda c, s, e: database.get_prices(c, s, e))
    tags = database.get_all_trade_tags()
    experiments = experiment_history()
    metadata = reproducibility_metadata(
        report_type,
        {"source": "local sqlite"},
        {"trades": len(trades), "experiments": len(experiments), "tags": len(tags)},
    )

    if report_type == "trade review report":
        by_tag = tag_statistics(analyzed, tags)
        category = by_category(analyzed)
        confidence = by_confidence(analyzed)
        markdown = build_trade_review_report(
            overall_report(analyzed),
            by_tag,
            category,
            confidence,
            learning_insights(analyzed, tags),
        )
        return markdown, by_tag if not by_tag.empty else analyzed, metadata

    if report_type == "strategy backtest report":
        return build_strategy_report(experiments), experiments, metadata

    if report_type == "factor research report":
        factor_summary = _factor_summary_placeholder()
        return build_factor_report(factor_summary), factor_summary, metadata

    if report_type == "portfolio report":
        metrics = {"note": "Run Portfolio Lab for latest portfolio metrics."}
        weights = pd.DataFrame(columns=["code", "name", "category", "target_weight"])
        markdown = build_markdown_report(
            "Portfolio Report",
            {"Metrics": metrics, "Weights": weights},
        )
        return markdown, weights, metadata

    sections = {
        "Trade Review": overall_report(analyzed),
        "Strategy Experiments": experiments,
        "Learning Insights": learning_insights(analyzed, tags),
        "Reproducibility": metadata,
    }
    export_df = experiments if not experiments.empty else analyzed
    return build_monthly_learning_report(sections), export_df, metadata


def _factor_summary_placeholder() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "factor": "momentum_20d",
                "note": "Run Factor Research for current IC and quantile results.",
            }
        ]
    )
