"""
DRIFTGUARD Event Integrity & Cryptographic Security Page
Monitors Ed25519 digital signatures, timestamp freshness enforcement, and atomic SQLite replay protection.
"""

import streamlit as st
import pandas as pd
from dashboard.components.header import render_header
from dashboard.services.dashboard_service import DashboardService
from simulation.stream_controller import StreamController
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


def render_event_integrity_page():
    service = DashboardService()
    health = service.get_system_health()
    logs_df = service.get_integrity_logs(limit=150)

    render_header(
        title="CRYPTOGRAPHIC INTEGRITY & REPLAY DEFENSE",
        subtitle="Ed25519 Canonical Verification, Freshness Windows & Atomic SQLite Anti-Replay Ledger",
        system_status="ONLINE" if health["security"]["status"] == "ACTIVE" else "ERROR",
    )

    # Architecture Defense Boundary Flow
    st.markdown(
        f"""
        <div style="background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 1.25rem;">
            <div style="font-size: 0.82rem; font-weight: 700; color: #FFFFFF; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.6rem;">
                Zero-Trust Defense Verification Boundary
            </div>
            <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem;">
                <div style="background: rgba(41, 182, 161, 0.1); border: 1px solid {ACCENT_PRIMARY}; border-radius: 6px; padding: 0.6rem 0.8rem; text-align: center; flex: 1;">
                    <div style="color: {ACCENT_PRIMARY}; font-weight: 700;">1. INGESTION</div>
                    <div style="color: {TEXT_MUTED}; font-size: 0.7rem;">Pydantic Schema Validation</div>
                </div>
                <div style="color: {TEXT_MUTED}; font-weight: 700;">➔</div>
                <div style="background: rgba(41, 182, 161, 0.1); border: 1px solid {ACCENT_PRIMARY}; border-radius: 6px; padding: 0.6rem 0.8rem; text-align: center; flex: 1.2;">
                    <div style="color: {ACCENT_PRIMARY}; font-weight: 700;">2. Ed25519 SIGNATURE</div>
                    <div style="color: {TEXT_MUTED}; font-size: 0.7rem;">Canonical Payload Check</div>
                </div>
                <div style="color: {TEXT_MUTED}; font-weight: 700;">➔</div>
                <div style="background: rgba(41, 182, 161, 0.1); border: 1px solid {ACCENT_PRIMARY}; border-radius: 6px; padding: 0.6rem 0.8rem; text-align: center; flex: 1.1;">
                    <div style="color: {ACCENT_PRIMARY}; font-weight: 700;">3. FRESHNESS (300s)</div>
                    <div style="color: {TEXT_MUTED}; font-size: 0.7rem;">Clock Skew Boundary</div>
                </div>
                <div style="color: {TEXT_MUTED}; font-weight: 700;">➔</div>
                <div style="background: rgba(41, 182, 161, 0.1); border: 1px solid {ACCENT_PRIMARY}; border-radius: 6px; padding: 0.6rem 0.8rem; text-align: center; flex: 1.3;">
                    <div style="color: {ACCENT_PRIMARY}; font-weight: 700;">4. ATOMIC REPLAY</div>
                    <div style="color: {TEXT_MUTED}; font-size: 0.7rem;">SQLite Unique (Key, Nonce)</div>
                </div>
                <div style="color: {TEXT_MUTED}; font-weight: 700;">➔</div>
                <div style="background: rgba(227, 109, 99, 0.15); border: 1px solid {COLOR_CRITICAL}; border-radius: 6px; padding: 0.6rem 0.8rem; text-align: center; flex: 1.2;">
                    <div style="color: {COLOR_CRITICAL}; font-weight: 700;">FAIL: REJECT</div>
                    <div style="color: {TEXT_MUTED}; font-size: 0.7rem;">Logged & ML Blocked</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Interactive Attack Demonstrations (PART C Section 5 Requirement)
    st.markdown(
        f'<div style="font-size: 0.9rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.4rem;">'
        f'Interactive Security Attack Demonstrations</div>',
        unsafe_allow_html=True,
    )
    atk_c1, atk_c2, atk_c3 = st.columns([1.5, 1.5, 1.0])
    controller = StreamController()

    with atk_c1:
        if st.button("🚨 Simulate Replay Double-Spend Attack", key="sec_demo_replay", use_container_width=True):
            with st.spinner("Retransmitting captured authorization payload..."):
                controller.step(scenario=ScenarioType.UPI_REPLAY_ATTACK, count=6)
            st.toast("Replay attack executed: Duplicate nonce and event ID blocked by SQLite ledger.")
            st.rerun()

    with atk_c2:
        if st.button("🚨 Simulate In-Flight Payload Tampering (MITM)", key="sec_demo_tamper", use_container_width=True):
            with st.spinner("Injecting modified payload with mismatched signature..."):
                controller.trigger_single_scenario(scenario=ScenarioType.UPI_TAMPERED, tamper=True)
            st.toast("Tamper attack executed: Signature verification failed. ML execution bypassed.")
            st.rerun()

    with atk_c3:
        if st.button("🔄 Refresh Audit Logs", key="sec_refresh_btn", use_container_width=True):
            st.rerun()

    st.markdown("<hr style='border: 1px solid #2A3C48; margin: 0.6rem 0 1rem 0;'>", unsafe_allow_html=True)

    # Security Incident Metrics
    s1, s2, s3, s4, s5 = st.columns(5)
    total_checks = len(logs_df)
    valid_checks = len(logs_df[logs_df["status"] == "VALID"]) if not logs_df.empty else 0
    bad_sigs = len(logs_df[logs_df["status"] == "REJECTED_BAD_SIG"]) if not logs_df.empty else 0
    expired_cnt = len(logs_df[logs_df["status"] == "REJECTED_EXPIRED"]) if not logs_df.empty else 0
    replay_cnt = len(logs_df[logs_df["status"].str.contains("REPLAY", na=False)]) if not logs_df.empty else 0

    with s1:
        st.metric("Total Verifications", f"{total_checks}")
    with s2:
        st.metric("Authorized & Valid", f"{valid_checks}", "Passed Security")
    with s3:
        b_col = COLOR_CRITICAL if bad_sigs > 0 else TEXT_MAIN
        st.metric("Tampered Signatures", f"{bad_sigs}", "MITM Attacks", delta_color="inverse")
    with s4:
        st.metric("Expired / Skewed", f"{expired_cnt}", "> 300s Stale")
    with s5:
        r_col = COLOR_CRITICAL if replay_cnt > 0 else TEXT_MAIN
        st.metric("Replay Attacks", f"{replay_cnt}", "Nonce / Event Duplicates")

    # Security Audit Log Table
    st.markdown(
        f'<div style="font-size: 1rem; font-weight: 700; color: #FFFFFF; margin-top: 1rem; margin-bottom: 0.4rem;">'
        f'Cryptographic Verification Audit Trail <span style="font-size: 0.8rem; font-weight: 500; color: {TEXT_MUTED};">'
        f'({len(logs_df)} Records Recorded in SQLite)</span></div>',
        unsafe_allow_html=True,
    )

    if logs_df.empty:
        st.info("No security verifications recorded yet. Run a simulation scenario or security test to generate logs.")
    else:
        # Status filter
        c_filter, c_spacer = st.columns([1, 2])
        with c_filter:
            status_f = st.selectbox(
                "Filter Log Status",
                ["ALL", "REJECTED_BAD_SIG", "REJECTED_REPLAY_EVENT_ID", "REJECTED_REPLAY_NONCE", "REJECTED_EXPIRED", "VALID"],
                key="sec_status_filter",
            )

        filtered_logs = logs_df.copy()
        if status_f != "ALL":
            filtered_logs = filtered_logs[filtered_logs["status"] == status_f]

        disp_logs = filtered_logs[["id", "event_id", "key_id", "nonce", "timestamp", "status", "reason"]].copy()
        disp_logs["timestamp"] = pd.to_datetime(disp_logs["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        disp_logs["nonce"] = disp_logs["nonce"].apply(lambda n: str(n)[:16] + "...")
        disp_logs = disp_logs.rename(columns={
            "id": "Log ID",
            "event_id": "Event ID",
            "key_id": "Public Key ID",
            "nonce": "Nonce",
            "timestamp": "Verification Time",
            "status": "Integrity Result",
            "reason": "Detailed Reason",
        })

        st.dataframe(disp_logs, use_container_width=True, height=300, hide_index=True)

        # Inspection of a Security Incident
        rejected_only = filtered_logs[filtered_logs["status"] != "VALID"]
        if not rejected_only.empty:
            st.markdown(
                f'<div style="font-size: 0.9rem; font-weight: 700; color: #FFFFFF; margin-top: 0.8rem; margin-bottom: 0.3rem;">'
                f'Security Incident Deep-Dive</div>',
                unsafe_allow_html=True,
            )
            sel_inc = st.selectbox("Select Incident to Inspect", rejected_only["event_id"].tolist(), key="sec_sel_inc")
            inc_rec = rejected_only[rejected_only["event_id"] == sel_inc].iloc[0]

            st.markdown(
                f"""
                <div style="background-color: {CARD_BG}; border: 1px solid {COLOR_CRITICAL}; border-radius: 6px; padding: 1rem; font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem;">
                    <div style="color: {COLOR_CRITICAL}; font-weight: 700; margin-bottom: 0.3rem;">[ATTACK INTERCEPTED] {inc_rec['status']}</div>
                    <div style="color: #D1DDE5; margin-bottom: 0.4rem;"><b>EVENT ID:</b> {inc_rec['event_id']}</div>
                    <div style="color: #D1DDE5; margin-bottom: 0.4rem;"><b>KEY ID:</b> {inc_rec['key_id']}</div>
                    <div style="color: #D1DDE5; margin-bottom: 0.4rem;"><b>NONCE:</b> {inc_rec['nonce']}</div>
                    <div style="color: #D1DDE5; margin-bottom: 0.4rem;"><b>REASON:</b> <span style="color: {COLOR_WARNING};">{inc_rec['reason']}</span></div>
                    <div style="color: {TEXT_MUTED}; font-size: 0.72rem; margin-top: 0.5rem;">
                        [SECURITY ENFORCEMENT] Untrusted payload blocked at perimeter boundary. ML scoring skipped.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

