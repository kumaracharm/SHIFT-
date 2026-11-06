"""
DRIFTGUARD Event Table & Inspection Component
Displays formatted security transactions, color-coded risk badges, and deep evidence inspection.
"""

from typing import Optional, Dict, Any
import json
import pandas as pd
import streamlit as st
from dashboard.theme import (
    CARD_BG,
    BORDER_COLOR,
    ACCENT_PRIMARY,
    ACCENT_SECONDARY,
    COLOR_WARNING,
    COLOR_CRITICAL,
    TEXT_MUTED,
)


def render_decision_badge(decision: str) -> str:
    """Returns HTML badge for decision rating."""
    badge_classes = {
        "NORMAL": "badge-normal",
        "MONITOR": "badge-monitor",
        "REVIEW": "badge-review",
        "HIGH_RISK": "badge-critical",
        "INTEGRITY_REJECTED": "badge-rejected",
    }
    cls = badge_classes.get(decision, "badge-normal")
    return f'<span class="badge {cls}">{decision}</span>'


def render_evidence_panel(evidence_items: list):
    """Renders human-readable evidence cards."""
    if not evidence_items:
        st.markdown(
            f'<div style="color: {TEXT_MUTED}; font-size: 0.85rem;">No anomalous evidence triggered.</div>',
            unsafe_allow_html=True,
        )
        return

    for item in evidence_items:
        factor = item.get("factor", "UNKNOWN")
        severity = item.get("severity", "INFO")
        detail = item.get("detail", "")

        border_col = COLOR_CRITICAL if severity in ("CRITICAL", "HIGH") else (
            COLOR_WARNING if severity == "MEDIUM" else ACCENT_PRIMARY
        )

        st.markdown(
            f"""
            <div style="background-color: {CARD_BG}; border-left: 3px solid {border_col}; 
                        border-top: 1px solid {BORDER_COLOR}; border-right: 1px solid {BORDER_COLOR};
                        border-bottom: 1px solid {BORDER_COLOR};
                        border-radius: 4px; padding: 0.6rem 0.85rem; margin-bottom: 0.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.2rem;">
                    <span style="font-size: 0.75rem; font-weight: 700; font-family: 'IBM Plex Mono', monospace; color: #FFFFFF;">
                        {factor}
                    </span>
                    <span style="font-size: 0.7rem; font-weight: 600; color: {border_col}; font-family: 'IBM Plex Mono', monospace;">
                        [{severity}]
                    </span>
                </div>
                <div style="font-size: 0.82rem; color: #D1DDE5;">
                    {detail}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_event_table_with_selector(df: pd.DataFrame, key_prefix: str = "evt_table"):
    """Renders an interactive event table with row selection to inspect evidence."""
    if df.empty:
        st.info("No transaction events recorded yet. Run a simulation scenario to populate telemetry.")
        return None

    # Prepare display dataframe
    display_df = df[[
        "event_id", "timestamp", "amount", "fraud_probability",
        "anomaly_score", "context_risk", "decision"
    ]].copy()

    display_df["timestamp"] = pd.to_datetime(display_df["timestamp"]).dt.strftime("%H:%M:%S UTC")
    display_df["amount"] = display_df["amount"].apply(lambda v: f"${v:,.2f}")
    display_df["fraud_probability"] = display_df["fraud_probability"].apply(lambda v: f"{v:.1%}")
    display_df["anomaly_score"] = display_df["anomaly_score"].apply(lambda v: f"{v:.2f}")
    display_df["context_risk"] = display_df["context_risk"].apply(lambda v: f"{v:.2f}")

    display_df = display_df.rename(columns={
        "event_id": "Event ID",
        "timestamp": "Time",
        "amount": "Amount",
        "fraud_probability": "Fraud Prob",
        "anomaly_score": "HST Anomaly",
        "context_risk": "Context Risk",
        "decision": "Decision",
    })

    st.dataframe(
        display_df,
        use_container_width=True,
        height=320,
        hide_index=True,
    )

