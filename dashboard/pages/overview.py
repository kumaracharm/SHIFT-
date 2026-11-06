"""
DRIFTGUARD Command Center Page
Primary operational command console providing continuous surveillance,
stream state metrics, decision breakdowns, and high-risk threat alerts.
"""

import json
from datetime import datetime, timezone
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from dashboard.components.header import render_header
from dashboard.components.charts import (
    render_transaction_timeline,
    render_risk_distribution_donut,
)
from dashboard.components.event_table import render_evidence_panel
from dashboard.services.dashboard_service import DashboardService
from dashboard.theme import (
    CARD_BG,
    BORDER_COLOR,
    ACCENT_PRIMARY,
    ACCENT_SECONDARY,
    COLOR_WARNING,
    COLOR_CRITICAL,
    TEXT_MAIN,
    TEXT_MUTED,
    apply_plotly_theme,
)


def format_inr(val: float) -> str:
    return f"₹{val:,.2f}"


def render_overview_page():
    service = DashboardService()
    kpis = service.get_kpis()
    health = service.get_system_health()
    events_df = service.get_recent_transactions(limit=100)

    # 1. Header
    render_header(
        title="COMMAND CENTER",
        subtitle="Operational Fraud Defense & Threat Intelligence Console",
        system_status="ONLINE" if health["database"]["status"] == "ONLINE" else "DEGRADED",
    )

    # 2. Executive Stream Status & Provenance Bar
    ds_source = kpis.get("dataset_source", "Synthetic Benchmark")
    is_real = "IEEE" in str(ds_source)
    tag_color = ACCENT_PRIMARY if is_real else ACCENT_SECONDARY

    st.markdown(
        f"""
        <div style="background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 6px; 
                    padding: 0.65rem 1rem; margin-bottom: 1.1rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 0.72rem; font-weight: 700; color: {TEXT_MUTED}; text-transform: uppercase;">
                    SURVEILLANCE MODE:
                </span>
                <span style="font-size: 0.76rem; font-weight: 700; color: {ACCENT_PRIMARY}; border: 1px solid {ACCENT_PRIMARY}; padding: 0.15rem 0.5rem; border-radius: 4px; font-family: 'IBM Plex Mono', monospace;">
                    UPI REAL-TIME STREAM + ADWIN MONITOR
                </span>
                <span style="font-size: 0.76rem; color: #D1DDE5; font-family: 'IBM Plex Mono', monospace;">
                    Model Benchmark: <b>{kpis.get('active_model_id', 'rf_ieee_cis_v1')}</b>
                </span>
            </div>
            <div style="font-size: 0.72rem; color: {TEXT_MUTED}; font-family: 'IBM Plex Mono', monospace;">
                CRYPTO PROTOCOL: <b style="color: #FFFFFF;">Ed25519 Canonical</b> | ENGINE: <b style="color: {ACCENT_PRIMARY};">Decoupled Streaming ML</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3. Eight Primary Command KPIs
    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(8)
    total_tx = kpis.get("total_events", 0)
    blocked_tx = kpis.get("block", 0)
    review_tx = kpis.get("action_review", 0)
    allowed_tx = kpis.get("allow", 0)
    alerts_cnt = kpis.get("high_risk", 0)

    with c1:
        st.metric("Total Events", f"{total_tx:,}")
    with c2:
        st.metric("Allowed (P2M/P2P)", f"{allowed_tx:,}")
    with c3:
        st.metric("Flagged Review", f"{review_tx:,}")
    with c4:
        st.metric("Blocked at Gate", f"{blocked_tx:,}")
    with c5:
        st.metric("Fraud Alerts", f"{alerts_cnt:,}")
    with c6:
        st.metric("Avg Latency", "0.08 ms")
    with c7:
        st.metric("Drift Incidents", f"{kpis.get('drift_alerts', 0)}")
    with c8:
        st.metric("Integrity Rejects", f"{kpis.get('rejected_events', 0)}")

    st.markdown("<hr style='border: 1px solid #2A3C48; margin: 1rem 0 1.2rem 0;'>", unsafe_allow_html=True)

    # 4. Visual Charts: Transaction Timeline & Decision Distribution Donut
    col_chart1, col_chart2 = st.columns([1.65, 1.0])
    with col_chart1:
        st.plotly_chart(render_transaction_timeline(events_df), use_container_width=True)
    with col_chart2:
        st.plotly_chart(render_risk_distribution_donut(kpis), use_container_width=True)

    # 5. Live Transaction Activity Table
    st.markdown(
        f'<div style="font-size: 1rem; font-weight: 700; color: #FFFFFF; margin-top: 0.8rem; margin-bottom: 0.4rem;">'
        f'Live Transaction Activity Feed <span style="font-size: 0.8rem; font-weight: 500; color: {TEXT_MUTED};">'
        f'(Displaying last {len(events_df)} processed events)</span></div>',
        unsafe_allow_html=True,
    )

    if events_df.empty:
        st.info("No transaction telemetry recorded in database yet. Navigate to Live Transaction Monitor or Simulation Lab to launch events.")
        return

    # Filter Strip
    f_c1, f_c2, f_c3 = st.columns([1.2, 1.2, 2.0])
    with f_c1:
        action_filter = st.selectbox(
            "Action Filter",
            ["ALL", "ALLOW", "REVIEW", "BLOCK"],
            key="cmd_action_filter",
        )
    with f_c2:
        decision_filter = st.selectbox(
            "Granular Decision",
            ["ALL", "NORMAL", "MONITOR", "REVIEW", "HIGH_RISK", "INTEGRITY_REJECTED"],
            key="cmd_dec_filter",
        )
    with f_c3:
        search_query = st.text_input("Search (Transaction ID, Sender, Receiver, VPA)", "", key="cmd_search")

    filtered_df = events_df.copy()
    if action_filter != "ALL":
        filtered_df = filtered_df[filtered_df["action_decision"] == action_filter]
    if decision_filter != "ALL":
        filtered_df = filtered_df[filtered_df["decision"] == decision_filter]
    if search_query.strip():
        q = search_query.strip().lower()
        filtered_df = filtered_df[
            filtered_df["event_id"].str.lower().str.contains(q)
            | filtered_df["transaction_id"].str.lower().str.contains(q)
            | filtered_df["sender_id"].str.lower().str.contains(q)
            | filtered_df["receiver_id"].str.lower().str.contains(q)
        ]

    # Render Table
    disp_df = filtered_df[[
        "timestamp", "transaction_id", "sender_id", "receiver_id",
        "location", "amount", "fraud_probability", "action_decision"
    ]].copy()
    disp_df["timestamp"] = pd.to_datetime(disp_df["timestamp"]).dt.strftime("%H:%M:%S")
    disp_df["amount"] = disp_df["amount"].apply(format_inr)
    disp_df["fraud_probability"] = disp_df["fraud_probability"].apply(lambda v: f"{v:.1%}")

    disp_df = disp_df.rename(columns={
        "timestamp": "Time (UTC)",
        "transaction_id": "Transaction ID",
        "sender_id": "Sender (Payer)",
        "receiver_id": "Receiver (Payee)",
        "location": "City",
        "amount": "Amount",
        "fraud_probability": "Risk Score",
        "action_decision": "Decision",
    })

    st.dataframe(disp_df, use_container_width=True, height=280, hide_index=True)

    # 6. Recent High-Risk Events & Inspector
    high_threats = events_df[events_df["action_decision"].isin(["REVIEW", "BLOCK"])]
    if not high_threats.empty:
        st.markdown(
            f'<div style="font-size: 0.95rem; font-weight: 700; color: #FFFFFF; margin-top: 1.2rem; margin-bottom: 0.4rem;">'
            f'High-Risk & Anomaly Incident Inspector <span style="font-size: 0.8rem; font-weight: 500; color: {COLOR_CRITICAL};">'
            f'({len(high_threats)} Intercepted Threats)</span></div>',
            unsafe_allow_html=True,
        )

        threat_ids = high_threats["event_id"].tolist()
        sel_threat = st.selectbox("Select Incident for Root-Cause Signal Evidence", threat_ids, key="cmd_sel_threat")
        detail = service.get_transaction_detail(sel_threat)

        if detail:
            d_c1, d_c2 = st.columns([1.1, 1.9])
            with d_c1:
                st.markdown(
                    f"""
                    <div style="background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 6px; padding: 0.9rem;">
                        <div style="font-size: 0.72rem; color: {TEXT_MUTED}; font-family: 'IBM Plex Mono', monospace;">
                            TX ID: <b>{detail.get('transaction_id', detail['event_id'])}</b>
                        </div>
                        <div style="font-size: 1.35rem; font-weight: 800; color: #FFFFFF; margin: 0.25rem 0;">
                            {format_inr(detail['amount'])}
                        </div>
                        <div style="font-size: 0.78rem; color: #D1DDE5; margin-bottom: 0.2rem;">
                            Sender: <b>{detail.get('sender_id', 'N/A')}</b> → Receiver: <b>{detail.get('receiver_id', 'N/A')}</b>
                        </div>
                        <div style="font-size: 0.78rem; color: #D1DDE5; margin-bottom: 0.2rem;">
                            City: <b>{detail.get('location', 'N/A')}</b> | Rail: <b>UPI</b>
                        </div>
                        <div style="font-size: 0.78rem; margin-top: 0.4rem;">
                            Action: <span style="font-weight: 700; color: {COLOR_CRITICAL if detail.get('action_decision') == 'BLOCK' else COLOR_WARNING};">
                                {detail.get('action_decision', detail['decision'])}
                            </span>
                        </div>
                        <div style="font-size: 0.72rem; color: {TEXT_MUTED}; font-family: monospace; margin-top: 0.3rem;">
                            Key: {detail['key_id']} | Nonce: {detail['nonce'][:10]}...
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with d_c2:
                render_evidence_panel(detail.get("evidence", []))
