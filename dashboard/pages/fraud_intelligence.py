"""
DRIFTGUARD Fraud Intelligence Page
In-depth fraud pattern analysis, supervised score distribution, multi-signal risk correlation,
and clear separation between rule-triggered alerts vs model-generated predictions.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from dashboard.components.header import render_header
from dashboard.components.charts import render_fraud_prob_vs_anomaly_scatter
from dashboard.components.event_table import render_evidence_panel
from dashboard.services.dashboard_service import DashboardService
from dashboard.theme import (
    apply_plotly_theme,
    CARD_BG,
    BORDER_COLOR,
    ACCENT_PRIMARY,
    ACCENT_SECONDARY,
    COLOR_WARNING,
    COLOR_CRITICAL,
    TEXT_MAIN,
    TEXT_MUTED,
)


def format_inr(val: float) -> str:
    return f"₹{val:,.2f}"


def render_fraud_intelligence_page():
    service = DashboardService()
    health = service.get_system_health()

    render_header(
        title="FRAUD INTELLIGENCE & PATTERN DECOMPOSITION",
        subtitle="Multi-Signal Threat Attribution, Rule vs Model Signal Separation & Evidence Audit",
        system_status="ONLINE" if health["database"]["status"] == "ONLINE" else "DEGRADED",
    )

    df = service.get_recent_transactions(limit=150)

    if df.empty:
        st.warning("No transaction telemetry available to analyze. Execute simulation scenarios to generate intelligence data.")
        return

    # Architectural Rule vs Model Distinction Banner (PART C Requirement)
    st.markdown(
        f"""
        <div style="background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 8px; padding: 0.85rem 1.1rem; margin-bottom: 1.1rem;">
            <div style="font-size: 0.88rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.4rem;">
                DUAL THREAT DETECTION TAXONOMY
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 0.78rem;">
                <div style="background-color: rgba(41, 182, 161, 0.08); border-left: 3px solid {ACCENT_PRIMARY}; padding: 0.5rem 0.8rem; border-radius: 4px;">
                    <b style="color: {ACCENT_PRIMARY};">RULE-BASED DETERMINISTIC GUARDS:</b><br>
                    • Velocity Spike Thresholds (> 6 tx/min to same VPA)<br>
                    • Impossible Location Jump / VPN Detection<br>
                    • Ed25519 Cryptographic Signature & Nonce Verification
                </div>
                <div style="background-color: rgba(232, 180, 91, 0.08); border-left: 3px solid {COLOR_WARNING}; padding: 0.5rem 0.8rem; border-radius: 4px;">
                    <b style="color: {COLOR_WARNING};">MACHINE LEARNING INFERENCE:</b><br>
                    • Supervised Fraud Classifier (Random Forest Probability)<br>
                    • Unsupervised Streaming Anomaly Detector (River HST)<br>
                    • ADWIN Statistical Drift & Covariate Shift Monitors
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Section 1: Overview KPIs
    k1, k2, k3, k4 = st.columns(4)
    total_eval = len(df)
    high_threats_df = df[df["action_decision"].isin(["REVIEW", "BLOCK"])]
    blocked_df = df[df["action_decision"] == "BLOCK"]

    with k1:
        st.metric("Total Analyzed", f"{total_eval:,}")
    with k2:
        st.metric("Threats Intercepted", f"{len(high_threats_df):,}", f"{(len(high_threats_df)/max(1, total_eval)):.1%}")
    with k3:
        st.metric("Transactions Blocked", f"{len(blocked_df):,}")
    with k4:
        avg_amt_high = high_threats_df["amount"].mean() if not high_threats_df.empty else 0.0
        st.metric("Avg Threat Amount", format_inr(avg_amt_high))

    # Section 2: Distribution Charts
    c_left, c_right = st.columns([1.1, 1.3])

    with c_left:
        # Fraud Probability Histogram
        fig_hist = go.Figure()
        fig_hist.add_trace(
            go.Histogram(
                x=df["fraud_probability"],
                nbinsx=20,
                marker=dict(color=ACCENT_PRIMARY, line=dict(color=CARD_BG, width=1)),
                opacity=0.85,
                name="Fraud Probability",
            )
        )
        fig_hist.add_vline(x=0.75, line_dash="dash", line_color=COLOR_CRITICAL, annotation_text="High Risk Threshold (0.75)")
        fig_hist.add_vline(x=0.40, line_dash="dash", line_color=COLOR_WARNING, annotation_text="Review Threshold (0.40)")
        fig_hist.update_layout(
            title=dict(text="Supervised Fraud Probability Distribution", font=dict(size=14, color=TEXT_MAIN)),
            xaxis_title="Fraud Probability Score",
            yaxis_title="Transaction Count",
        )
        st.plotly_chart(apply_plotly_theme(fig_hist, height=310), use_container_width=True)

    with c_right:
        # 2D Scatter: Supervised Fraud Probability vs Streaming Anomaly
        st.plotly_chart(render_fraud_prob_vs_anomaly_scatter(df), use_container_width=True)

    # Section 3: High-Risk Threat Register
    st.markdown(
        f'<div style="font-size: 1rem; font-weight: 700; color: #FFFFFF; margin-top: 1rem; margin-bottom: 0.4rem;">'
        f'Critical Threat Register <span style="font-size: 0.8rem; font-weight: 500; color: {COLOR_CRITICAL};">'
        f'({len(high_threats_df)} Flagged Threats)</span></div>',
        unsafe_allow_html=True,
    )

    if high_threats_df.empty:
        st.success("No High-Risk transactions recorded in recent stream. Normal traffic patterns prevailing.")
    else:
        disp_high = high_threats_df[[
            "timestamp", "transaction_id", "sender_id", "receiver_id", "location",
            "amount", "fraud_probability", "anomaly_score", "action_decision"
        ]].copy()
        disp_high["timestamp"] = pd.to_datetime(disp_high["timestamp"]).dt.strftime("%H:%M:%S UTC")
        disp_high["amount"] = disp_high["amount"].apply(format_inr)
        disp_high["fraud_probability"] = disp_high["fraud_probability"].apply(lambda v: f"{v:.1%}")
        disp_high["anomaly_score"] = disp_high["anomaly_score"].apply(lambda v: f"{v:.2f}")

        disp_high = disp_high.rename(columns={
            "timestamp": "Time",
            "transaction_id": "Transaction ID",
            "sender_id": "Payer",
            "receiver_id": "Payee",
            "location": "City",
            "amount": "Amount",
            "fraud_probability": "Fraud Prob",
            "anomaly_score": "HST Anomaly",
            "action_decision": "Decision",
        })

        st.dataframe(disp_high, use_container_width=True, height=220, hide_index=True)

        # Deep Threat Investigation
        threat_ids = high_threats_df["event_id"].tolist()
        sel_threat = st.selectbox("Select Threat for Root-Cause Signal Attribution", threat_ids, key="fi_sel_threat")
        detail = service.get_transaction_detail(sel_threat)

        if detail:
            st.markdown(
                f"""
                <div style="background-color: {CARD_BG}; border: 1px solid {COLOR_CRITICAL}; border-radius: 8px; padding: 1rem; margin-top: 0.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="font-size: 0.85rem; font-weight: 700; color: {COLOR_CRITICAL}; font-family: 'IBM Plex Mono', monospace;">
                            INCIDENT: {detail.get('transaction_id', detail['event_id'])}
                        </span>
                        <span style="font-size: 0.8rem; font-weight: 600; color: #FFFFFF;">
                            Amount: <span style="font-family: 'IBM Plex Mono', monospace; color: {COLOR_CRITICAL}; font-size: 1.1rem;">{format_inr(detail['amount'])}</span>
                        </span>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 0.8rem; font-size: 0.78rem; font-family: 'IBM Plex Mono', monospace;">
                        <div style="background-color: rgba(0,0,0,0.2); padding: 0.5rem; border-radius: 4px;"><b>SENDER:</b> {detail.get('sender_id', 'N/A')}</div>
                        <div style="background-color: rgba(0,0,0,0.2); padding: 0.5rem; border-radius: 4px;"><b>RECEIVER:</b> {detail.get('receiver_id', 'N/A')}</div>
                        <div style="background-color: rgba(0,0,0,0.2); padding: 0.5rem; border-radius: 4px;"><b>LOCATION:</b> {detail.get('location', 'N/A')}</div>
                        <div style="background-color: rgba(0,0,0,0.2); padding: 0.5rem; border-radius: 4px;"><b>INTEGRITY:</b> {detail['integrity_status']}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(f'<div style="font-size: 0.85rem; font-weight: 700; color: #FFFFFF; margin-top: 0.5rem; margin-bottom: 0.3rem;">EXPLAINABLE AUDIT EVIDENCE</div>', unsafe_allow_html=True)
            render_evidence_panel(detail.get("evidence", []))
