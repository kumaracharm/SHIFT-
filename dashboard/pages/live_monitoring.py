"""
DRIFTGUARD Live Transaction Monitor Page
Main operational demonstration screen providing real-time UPI transaction streaming,
interactive operator control panel (Start, Pause, Resume, Stop, Reset, Inject, Export),
and granular transaction inspector.
"""

import time
import json
import streamlit as st
import pandas as pd

from dashboard.components.header import render_header
from dashboard.components.event_table import render_evidence_panel
from dashboard.components.charts import render_live_stream_timeseries, render_threat_gauge
from dashboard.services.dashboard_service import DashboardService
from simulation.stream_controller import StreamController, StreamState
from simulation.scenarios import ScenarioType
from dashboard.theme import (
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


def render_live_monitoring_page():
    service = DashboardService()
    health = service.get_system_health()
    controller = StreamController()

    render_header(
        title="LIVE TRANSACTION MONITOR",
        subtitle="Continuous Real-Time UPI Payment Surveillance & Security Enforcement Console",
        system_status="ONLINE" if health["database"]["status"] == "ONLINE" else "DEGRADED",
    )

    # Initialize Session State Controls
    if "stream_status" not in st.session_state:
        st.session_state["stream_status"] = StreamState.STOPPED
    if "selected_scenario" not in st.session_state:
        st.session_state["selected_scenario"] = ScenarioType.UPI_NORMAL
    if "stream_rate" not in st.session_state:
        st.session_state["stream_rate"] = 5
    if "stream_intensity" not in st.session_state:
        st.session_state["stream_intensity"] = 0.08

    status = st.session_state["stream_status"]

    # PART B: Operator Control Panel
    st.markdown(
        f"""
        <div style="background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 8px; padding: 0.8rem 1.1rem; margin-bottom: 1.1rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
                <span style="font-size: 0.88rem; font-weight: 700; color: #FFFFFF; font-family: 'IBM Plex Mono', monospace;">
                    OPERATOR STREAM CONTROL PANEL
                </span>
                <span style="font-size: 0.75rem; font-weight: 700; font-family: monospace; padding: 0.2rem 0.6rem; border-radius: 4px;
                             border: 1px solid {'#29B6A1' if status == StreamState.RUNNING else ('#E8B45B' if status == StreamState.PAUSED else '#9EAFBA')};
                             color: {'#29B6A1' if status == StreamState.RUNNING else ('#E8B45B' if status == StreamState.PAUSED else '#9EAFBA')};">
                    FEED STATE: {status.value}
                </span>
            </div>
            <div style="font-size: 0.76rem; color: #D1DDE5;">
                Governs streaming UPI transaction generation, cryptographic signing, decoupled scoring, and SQLite persistence.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Stream Controls Row
    btn_c1, btn_c2, btn_c3, btn_c4, btn_c5, btn_c6 = st.columns([1.1, 1.0, 1.0, 1.0, 1.3, 1.3])

    with btn_c1:
        if st.button("▶ Start Stream", key="op_start", type="primary", disabled=(status == StreamState.RUNNING), use_container_width=True):
            st.session_state["stream_status"] = StreamState.RUNNING
            st.rerun()

    with btn_c2:
        if st.button("⏸ Pause", key="op_pause", disabled=(status != StreamState.RUNNING), use_container_width=True):
            st.session_state["stream_status"] = StreamState.PAUSED
            st.rerun()

    with btn_c3:
        if st.button("⏯ Resume", key="op_resume", disabled=(status != StreamState.PAUSED), use_container_width=True):
            st.session_state["stream_status"] = StreamState.RUNNING
            st.rerun()

    with btn_c4:
        if st.button("⏹ Stop", key="op_stop", disabled=(status == StreamState.STOPPED), use_container_width=True):
            st.session_state["stream_status"] = StreamState.STOPPED
            st.rerun()

    with btn_c5:
        if st.button("🔄 Reset Session", key="op_reset", use_container_width=True):
            st.session_state["stream_status"] = StreamState.STOPPED
            service.reset_simulation_data()
            st.success("Session tables cleared. Keystore and trained models preserved.")
            time.sleep(0.4)
            st.rerun()

    with btn_c6:
        csv_data = controller.export_csv(limit=500)
        st.download_button(
            label="📥 Export Session CSV",
            data=csv_data,
            file_name="driftguard_upi_session.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # Secondary Config & Injection Strip
    st.markdown("<div style='height: 0.4rem;'></div>", unsafe_allow_html=True)
    cfg_c1, cfg_c2, cfg_c3, cfg_c4 = st.columns([1.6, 1.0, 1.0, 1.4])

    with cfg_c1:
        scenario_options = [
            ScenarioType.UPI_NORMAL,
            ScenarioType.UPI_AMOUNT_SPIKE,
            ScenarioType.UPI_VELOCITY_BURST,
            ScenarioType.UPI_NEW_PAYEE,
            ScenarioType.UPI_DEVICE_CHANGE,
            ScenarioType.UPI_LOCATION_JUMP,
            ScenarioType.UPI_REPLAY_ATTACK,
            ScenarioType.UPI_TAMPERED,
            ScenarioType.UPI_MULE_RING,
        ]
        chosen_sc = st.selectbox(
            "Active Simulation Scenario",
            scenario_options,
            index=scenario_options.index(st.session_state["selected_scenario"]) if st.session_state["selected_scenario"] in scenario_options else 0,
            format_func=lambda s: s.value.replace("_", " ").upper(),
            key="op_sc_select",
        )
        st.session_state["selected_scenario"] = chosen_sc

    with cfg_c2:
        st.session_state["stream_rate"] = st.slider("Rate (tx/tick)", min_value=1, max_value=10, value=st.session_state["stream_rate"])

    with cfg_c3:
        st.session_state["stream_intensity"] = st.slider("Anomaly Ratio", min_value=0.0, max_value=0.5, value=st.session_state["stream_intensity"], step=0.05)

    with cfg_c4:
        st.write("")
        st.write("")
        if st.button("🚨 Inject Suspicious Event", key="btn_manual_inject", use_container_width=True):
            inj_res = controller.trigger_single_scenario(scenario=st.session_state["selected_scenario"])
            st.toast(f"Injected {inj_res['transaction_id']} -> Decision: {inj_res['decision']}")
            st.rerun()

    st.markdown("<hr style='border: 1px solid #2A3C48; margin: 0.8rem 0 1.2rem 0;'>", unsafe_allow_html=True)

    # Query Recent Transactions
    df = service.get_recent_transactions(limit=100)

    # Empty State Handling
    if df.empty:
        st.markdown(
            f"""
            <div style="background-color: {CARD_BG}; border: 1px dashed {BORDER_COLOR}; border-radius: 8px; padding: 2.5rem 1.5rem; text-align: center; margin: 1.5rem 0;">
                <div style="font-size: 1.8rem; margin-bottom: 0.5rem;">📡</div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.4rem;">
                    Stream Idle — No Active Transactions
                </div>
                <div style="font-size: 0.85rem; color: #D1DDE5; max-width: 450px; margin: 0 auto 1.2rem auto;">
                    The operator stream is currently stopped. Click <b>"Start Stream"</b> above or the quick button below to commence continuous real-time UPI monitoring.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c_emp1, c_emp2, c_emp3 = st.columns([1, 1.8, 1])
        with c_emp2:
            if st.button("🚀 Ingest Initial UPI Batch (15 Transactions)", key="btn_init_upi", type="primary", use_container_width=True):
                controller.step(scenario=ScenarioType.UPI_NORMAL, count=15)
                st.rerun()
        return

    # Visual Multi-Signal Telemetry Charts
    c_chart_main, c_chart_gauge = st.columns([2.2, 1.0])
    with c_chart_main:
        st.plotly_chart(render_live_stream_timeseries(df), use_container_width=True)
    with c_chart_gauge:
        high_cnt = sum(df["action_decision"].isin(["REVIEW", "BLOCK"]))
        threat_rate = (high_cnt / max(1, len(df))) * 100.0
        st.plotly_chart(render_threat_gauge(threat_rate), use_container_width=True)
        st.markdown(
            f"""
            <div style="background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 6px; padding: 0.6rem 0.8rem; font-size: 0.74rem; color: #D1DDE5; margin-top: -10px;">
                <b style="color: #FFFFFF;">SECURITY PROFILE:</b><br>
                • Protocol: <span style="color: {ACCENT_PRIMARY};">Ed25519 Asymmetric Auth</span><br>
                • Replay Protection: <span style="color: {ACCENT_SECONDARY};">Atomic SQLite Ledger</span><br>
                • ML Model: <span style="color: {COLOR_WARNING};">Supervised + River HST</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='border: 1px solid #2A3C48; margin: 0.8rem 0 1rem 0;'>", unsafe_allow_html=True)

    # PART C Section 2: Main Demonstration Screen - Continuously Updating Table + Inspector
    st.markdown(
        f'<div style="font-size: 0.98rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.5rem;">'
        f'Live Transaction Ledger <span style="font-size: 0.8rem; font-weight: 500; color: {TEXT_MUTED};">'
        f'(Showing last {len(df)} transactions)</span></div>',
        unsafe_allow_html=True,
    )

    col_table, col_detail = st.columns([1.7, 1.3])

    with col_table:
        disp_df = df[[
            "timestamp", "transaction_id", "sender_id", "receiver_id",
            "amount", "fraud_probability", "action_decision"
        ]].copy()

        disp_df["timestamp"] = pd.to_datetime(disp_df["timestamp"]).dt.strftime("%H:%M:%S")
        disp_df["amount"] = disp_df["amount"].apply(format_inr)
        disp_df["fraud_probability"] = disp_df["fraud_probability"].apply(lambda v: f"{v:.1%}")

        disp_df = disp_df.rename(columns={
            "timestamp": "Timestamp",
            "transaction_id": "Transaction ID",
            "sender_id": "Sender",
            "receiver_id": "Receiver",
            "amount": "Amount",
            "fraud_probability": "Risk",
            "action_decision": "Decision",
        })

        st.dataframe(disp_df, use_container_width=True, height=440, hide_index=True)

    with col_detail:
        st.markdown(
            f'<div style="font-size: 0.88rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.4rem;">'
            f'Transaction Deep Telemetry Inspector</div>',
            unsafe_allow_html=True,
        )

        event_ids = df["event_id"].tolist()
        tx_labels = {
            r["event_id"]: f"{r['transaction_id']} | {r['sender_id']} → {r['receiver_id']} | {format_inr(r['amount'])}"
            for _, r in df.iterrows()
        }

        sel_id = st.selectbox(
            "Select Transaction to Inspect",
            event_ids,
            format_func=lambda eid: tx_labels.get(eid, eid),
            key="lm_sel_tx",
        )

        detail = service.get_transaction_detail(sel_id)

        if detail:
            payload = detail.get("payload", {})
            synth_meta = payload.get("synthetic_metadata", {})
            action = detail.get("action_decision", detail.get("decision", "ALLOW"))
            action_color = ACCENT_PRIMARY if action == "ALLOW" else (COLOR_WARNING if action == "REVIEW" else COLOR_CRITICAL)

            st.markdown(
                f"""
                <div style="background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 6px; padding: 0.85rem; margin-bottom: 0.6rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                        <span style="font-size: 0.72rem; color: {TEXT_MUTED}; font-family: monospace;">TX ID: {detail.get('transaction_id', detail['event_id'])}</span>
                        <span style="font-size: 0.75rem; font-weight: 800; color: {action_color}; border: 1px solid {action_color}; padding: 0.1rem 0.5rem; border-radius: 4px; font-family: monospace;">
                            {action}
                        </span>
                    </div>
                    <div style="font-size: 1.4rem; font-weight: 800; color: #FFFFFF; margin: 0.2rem 0;">
                        {format_inr(detail['amount'])}
                    </div>
                    <div style="font-size: 0.78rem; color: #D1DDE5; margin-bottom: 0.2rem;">
                        <b>Payer:</b> {detail.get('sender_id', 'N/A')} ({synth_meta.get('sender_vpa', 'N/A')})
                    </div>
                    <div style="font-size: 0.78rem; color: #D1DDE5; margin-bottom: 0.2rem;">
                        <b>Payee:</b> {detail.get('receiver_id', 'N/A')} ({synth_meta.get('receiver_vpa', 'N/A')})
                    </div>
                    <div style="font-size: 0.78rem; color: #D1DDE5; margin-bottom: 0.4rem;">
                        <b>Location:</b> {detail.get('location', 'N/A')} | <b>Rail:</b> UPI | <b>Payee Status:</b> {synth_meta.get('payee_status', 'KNOWN')}
                    </div>
                    <div style="font-size: 0.72rem; color: {TEXT_MUTED}; border-top: 1px solid {BORDER_COLOR}; padding-top: 0.35rem; font-family: monospace;">
                        Integrity: <b>{detail['integrity_status']}</b> | Device Trust: <b>{synth_meta.get('device_trust', 'ESTABLISHED')}</b><br>
                        Ed25519 Key ID: {detail['key_id']} | Nonce: {detail['nonce'][:12]}...
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(f'<div style="font-size: 0.78rem; font-weight: 700; color: {TEXT_MUTED}; margin-bottom: 0.2rem;">DECISION EVIDENCE & AUDIT TRAIL</div>', unsafe_allow_html=True)
            render_evidence_panel(detail.get("evidence", []))

    # Safe Streamlit Periodic Refresh Loop (Only runs when status == RUNNING)
    if st.session_state["stream_status"] == StreamState.RUNNING:
        controller.step(
            scenario=st.session_state["selected_scenario"],
            count=st.session_state["stream_rate"],
            anomaly_ratio=st.session_state["stream_intensity"],
        )
        time.sleep(1.0)
        st.rerun()
