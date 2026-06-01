from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def price_chart(series: pd.DataFrame, buy_price: float, buy_date: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=series["trade_date"], y=series["close"], mode="lines", name="收盘价")
    )
    fig.add_trace(
        go.Scatter(
            x=[series.iloc[0]["trade_date"]],
            y=[buy_price],
            mode="markers",
            marker={"size": 11, "color": "#d62728"},
            name=f"买入点 {buy_date}",
        )
    )
    fig.update_layout(
        height=360, margin={"l": 20, "r": 20, "t": 30, "b": 20}, hovermode="x unified"
    )
    return fig


def return_chart(series: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=series["trade_date"], y=series["return_rate"], mode="lines", name="收益率")
    )
    fig.update_yaxes(tickformat=".1%")
    fig.update_layout(
        height=320, margin={"l": 20, "r": 20, "t": 30, "b": 20}, hovermode="x unified"
    )
    return fig


def drawdown_chart(series: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=series["trade_date"], y=series["drawdown"], fill="tozeroy", name="回撤")
    )
    fig.update_yaxes(tickformat=".1%")
    fig.update_layout(
        height=320, margin={"l": 20, "r": 20, "t": 30, "b": 20}, hovermode="x unified"
    )
    return fig


def distribution_chart(values: pd.Series, title: str) -> go.Figure:
    fig = go.Figure(go.Histogram(x=values.dropna()))
    fig.update_layout(title=title, height=300, margin={"l": 20, "r": 20, "t": 45, "b": 20})
    return fig


def benchmark_comparison(
    series: pd.DataFrame, benchmark_series: pd.DataFrame | None = None
) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=series["trade_date"], y=series["return_rate"], mode="lines", name="个股")
    )
    if benchmark_series is not None and not benchmark_series.empty:
        fig.add_trace(
            go.Scatter(
                x=benchmark_series["trade_date"],
                y=benchmark_series["benchmark_return"],
                mode="lines",
                name="基准",
            )
        )
    else:
        fig.add_trace(
            go.Scatter(x=series["trade_date"], y=[0] * len(series), mode="lines", name="基准 0%")
        )
    fig.update_yaxes(tickformat=".1%")
    fig.update_layout(
        height=320, margin={"l": 20, "r": 20, "t": 30, "b": 20}, hovermode="x unified"
    )
    return fig
