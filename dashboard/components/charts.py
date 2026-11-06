"""
DRIFTGUARD Charting Engine
Plotly data visualizations formatted with Graphite + Arctic Teal aesthetic.
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from dashboard.theme import (
    apply_plotly_theme,
    ACCENT_PRIMARY,
    ACCENT_SECONDARY,
    COLOR_WARNING,
    COLOR_CRITICAL,
    COLOR_INFO,
    CARD_BG,
    BORDER_COLOR,
    TEXT_MAIN,
    TEXT_MUTED,
)


def render_risk_distribution_donut(kpis: Dict[str, Any]) -> go.Figure:
    """Renders donut chart of risk decision classifications."""
    labels = ["Normal", "Monitor", "Review", "High Risk"]
    values = [
        kpis.get("normal", 0),
        kpis.get("monitor", 0),
        kpis.get("review", 0),
        kpis.get("high_risk", 0),
    ]
    colors = [ACCENT_PRIMARY, ACCENT_SECONDARY, COLOR_WARNING, COLOR_CRITICAL]

    # Handle all zero case
    if sum(values) == 0:
        values = [1, 0, 0, 0]
        labels = ["Awaiting Events", "Monitor", "Review", "High Risk"]
        colors = [BORDER_COLOR, BORDER_COLOR, BORDER_COLOR, BORDER_COLOR]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.68,
                marker=dict(colors=colors, line=dict(color=CARD_BG, width=2)),
                textinfo="percent+label",
                textposition="outside",
                hoverinfo="label+value+percent",
            )
        ]
    )
    fig.update_layout(
        title=dict(text="Risk Classification Breakdown", font=dict(size=14, color=TEXT_MAIN)),
        showlegend=False,
    )
    return apply_plotly_theme(fig, height=290)


def render_transaction_timeline(df: pd.DataFrame) -> go.Figure:
    """Renders transaction volume & amounts over time with risk coloring."""
    if df.empty or "timestamp" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="No transaction telemetry recorded yet.<br>Execute a scenario from the Simulation Lab.",
            showarrow=False,
            font=dict(size=13, color=TEXT_MUTED),
        )
        return apply_plotly_theme(fig, height=290)

    plot_df = df.copy()
    plot_df["timestamp"] = pd.to_datetime(plot_df["timestamp"])
    plot_df = plot_df.sort_values("timestamp")

    color_map = {
        "NORMAL": ACCENT_PRIMARY,
        "MONITOR": ACCENT_SECONDARY,
        "REVIEW": COLOR_WARNING,
        "HIGH_RISK": COLOR_CRITICAL,
        "INTEGRITY_REJECTED": "#FF4444",
    }

    fig = go.Figure()
    for decision, color in color_map.items():
        subset = plot_df[plot_df["decision"] == decision]
        if not subset.empty:
            fig.add_trace(
                go.Scatter(
                    x=subset["timestamp"],
                    y=subset["amount"],
                    mode="markers",
                    name=decision,
                    marker=dict(
                        color=color,
                        size=subset["fraud_probability"] * 10 + 6,
                        opacity=0.85,
                        line=dict(color=CARD_BG, width=1),
                    ),
                    hovertemplate="<b>Event ID:</b> %{customdata[0]}<br>"
                                  "<b>Time:</b> %{x|%H:%M:%S}<br>"
                                  "<b>Amount:</b> $%{y:.2f}<br>"
                                  "<b>Fraud Prob:</b> %{customdata[1]:.2f}<br>"
                                  "<b>Anomaly:</b> %{customdata[2]:.2f}<extra></extra>",
                    customdata=subset[["event_id", "fraud_probability", "anomaly_score"]].values,
                )
            )

    fig.update_layout(
        title=dict(text="Streaming Ingestion Timeline (Amount vs Time)", font=dict(size=14, color=TEXT_MAIN)),
        xaxis_title="UTC Timestamp",
        yaxis_title="Amount ($USD)",
    )
    return apply_plotly_theme(fig, height=290)


def render_fraud_prob_vs_anomaly_scatter(df: pd.DataFrame) -> go.Figure:
    """
    Renders 2D quadrant scatter separating Supervised Fraud Probability vs Streaming Anomaly Score.
    Visibly proves dimensional independence between supervised classification and unsupervised anomalies.
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No prediction records available.",
            showarrow=False,
            font=dict(size=13, color=TEXT_MUTED),
        )
        return apply_plotly_theme(fig, height=310)

    color_map = {
        "NORMAL": ACCENT_PRIMARY,
        "MONITOR": ACCENT_SECONDARY,
        "REVIEW": COLOR_WARNING,
        "HIGH_RISK": COLOR_CRITICAL,
    }

    fig = go.Figure()
    for decision, color in color_map.items():
        subset = df[df["decision"] == decision]
        if not subset.empty:
            fig.add_trace(
                go.Scatter(
                    x=subset["fraud_probability"],
                    y=subset["anomaly_score"],
                    mode="markers",
                    name=decision,
                    marker=dict(size=8, color=color, opacity=0.8),
                    hovertemplate="<b>Event:</b> %{customdata}<br>Fraud Prob: %{x:.2f}<br>HST Anomaly: %{y:.2f}<extra></extra>",
                    customdata=subset["event_id"],
                )
            )

    # Reference threshold lines
    fig.add_vline(x=0.75, line_dash="dash", line_color=COLOR_CRITICAL, opacity=0.5, annotation_text="High Risk Threshold (0.75)")
    fig.add_hline(y=0.65, line_dash="dash", line_color=COLOR_WARNING, opacity=0.5, annotation_text="Anomaly Threshold (0.65)")

    fig.update_layout(
        title=dict(text="Supervised Fraud Probability vs Streaming Anomaly Score", font=dict(size=14, color=TEXT_MAIN)),
        xaxis_title="Supervised Fraud Likelihood [Random Forest] (0.0 to 1.0)",
        yaxis_title="Unsupervised Streaming Anomaly [HalfSpaceTrees] (0.0 to 1.0)",
        xaxis=dict(range=[-0.05, 1.05]),
        yaxis=dict(range=[-0.05, 1.05]),
    )
    return apply_plotly_theme(fig, height=310)


def render_adwin_signal_chart(drift_df: pd.DataFrame) -> go.Figure:
    """Renders historical ADWIN drift detection events."""
    if drift_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="ADWIN monitoring active. No distribution drift triggered yet.<br>Simulate 'Fraud Pattern Shift' to observe drift alerts.",
            showarrow=False,
            font=dict(size=13, color=TEXT_MUTED),
        )
        return apply_plotly_theme(fig, height=270)

    fig = go.Figure()
    for signal_type, color in [("unlabelled_anomaly", ACCENT_SECONDARY), ("labelled_error", COLOR_WARNING)]:
        subset = drift_df[drift_df["signal_type"] == signal_type]
        if not subset.empty:
            fig.add_trace(
                go.Scatter(
                    x=subset["observation_count"],
                    y=subset["metric_value"],
                    mode="markers+lines",
                    name=signal_type.replace("_", " ").title(),
                    marker=dict(size=10, color=color, symbol="diamond"),
                    line=dict(color=color, width=1.5, dash="dot"),
                    hovertemplate="<b>Detector:</b> %{customdata}<br>Obs Index: %{x}<br>Shift Metric: %{y:.4f}<extra></extra>",
                    customdata=subset["detector_name"],
                )
            )

    fig.update_layout(
        title=dict(text="ADWIN Drift Detections Across Observation Steps", font=dict(size=14, color=TEXT_MAIN)),
        xaxis_title="Observation Count",
        yaxis_title="Signal Shift Magnitude",
    )
    return apply_plotly_theme(fig, height=270)


def render_live_stream_timeseries(df: pd.DataFrame) -> go.Figure:
    """
    Renders dynamic multi-signal streaming timeline with cursor crosshairs.
    Plots Transaction Amount (primary Y) alongside Fraud Likelihood and HST Anomaly (secondary Y).
    """
    if df.empty or "timestamp" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="Awaiting live stream transactions...",
            showarrow=False,
            font=dict(size=13, color=TEXT_MUTED),
        )
        return apply_plotly_theme(fig, height=310)

    plot_df = df.copy().sort_values("timestamp")
    plot_df["time_str"] = pd.to_datetime(plot_df["timestamp"]).dt.strftime("%H:%M:%S")

    fig = go.Figure()

    # 1. Transaction Amount (Bar / Area)
    fig.add_trace(
        go.Bar(
            x=plot_df["time_str"],
            y=plot_df["amount"],
            name="Amount ($USD)",
            marker_color="rgba(41, 182, 161, 0.35)",
            marker_line_color=ACCENT_PRIMARY,
            marker_line_width=1,
            yaxis="y1",
            hovertemplate="Amount: $%{y:,.2f}<extra></extra>",
        )
    )

    # 2. Supervised Fraud Probability (Line with markers)
    fig.add_trace(
        go.Scatter(
            x=plot_df["time_str"],
            y=plot_df["fraud_probability"],
            name="Fraud Probability",
            mode="lines+markers",
            line=dict(color=COLOR_CRITICAL, width=2.5),
            marker=dict(size=6, color=COLOR_CRITICAL),
            yaxis="y2",
            hovertemplate="Fraud Prob: %{y:.1%}<extra></extra>",
        )
    )

    # 3. Streaming River HST Anomaly Score (Line with markers)
    fig.add_trace(
        go.Scatter(
            x=plot_df["time_str"],
            y=plot_df["anomaly_score"],
            name="HST Anomaly Score",
            mode="lines+markers",
            line=dict(color=COLOR_WARNING, width=2, dash="dash"),
            marker=dict(size=5, color=COLOR_WARNING, symbol="diamond"),
            yaxis="y2",
            hovertemplate="Anomaly Score: %{y:.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(text="Real-Time Stream Multi-Signal Sensor (Amount vs Fraud & Anomaly Signals)", font=dict(size=14, color=TEXT_MAIN)),
        xaxis=dict(title="Stream Sequence Time (UTC)", tickangle=-30),
        yaxis=dict(
            title=dict(text="Transaction Amount ($)", font=dict(color=ACCENT_PRIMARY)),
            tickfont=dict(color=ACCENT_PRIMARY),
            side="left",
        ),
        yaxis2=dict(
            title=dict(text="Risk & Anomaly Scores (0.0 to 1.0)", font=dict(color=COLOR_WARNING)),
            tickfont=dict(color=COLOR_WARNING),
            overlaying="y",
            side="right",
            range=[-0.05, 1.05],
        ),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return apply_plotly_theme(fig, height=310)


def render_threat_gauge(threat_pct: float) -> go.Figure:
    """Renders real-time fleet threat level gauge (0 - 100%)."""
    val = min(100.0, max(0.0, threat_pct))
    bar_color = ACCENT_PRIMARY if val < 20 else (COLOR_WARNING if val < 50 else COLOR_CRITICAL)

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=val,
            number={"suffix": "%", "font": {"size": 28, "color": TEXT_MAIN, "family": "IBM Plex Mono, monospace"}},
            title={"text": "Live Fleet Threat Level", "font": {"size": 13, "color": TEXT_MUTED}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": BORDER_COLOR, "tickfont": {"size": 10, "color": TEXT_MUTED}},
                "bar": {"color": bar_color, "thickness": 0.3},
                "bgcolor": CARD_BG,
                "borderwidth": 1,
                "bordercolor": BORDER_COLOR,
                "steps": [
                    {"range": [0, 20], "color": "rgba(41, 182, 161, 0.15)"},
                    {"range": [20, 50], "color": "rgba(232, 180, 91, 0.15)"},
                    {"range": [50, 100], "color": "rgba(227, 109, 99, 0.2)"},
                ],
                "threshold": {
                    "line": {"color": COLOR_CRITICAL, "width": 3},
                    "thickness": 0.8,
                    "value": 75,
                },
            },
        )
    )
    fig.update_layout(
        margin=dict(l=25, r=25, t=40, b=15),
        height=170,
        paper_bgcolor=CARD_BG,
    )
    return fig

