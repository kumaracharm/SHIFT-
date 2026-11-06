"""
DRIFTGUARD Simulation Lab Page
Interactive simulation control center with Guided Hackathon Demonstration Mode,
UPI payment scenarios, and cryptographic security attack testing.
"""

import time
import json
import streamlit as st
import pandas as pd

from dashboard.components.header import render_header
from dashboard.services.simulation_service import SimulationService
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


def format_inr(val: float) -> str:
    return f"₹{val:,.2f}"


def render_simulation_lab_page():
    sim_service = SimulationService()
    dash_service = DashboardService()
    controller = StreamController()
    health = dash_service.get_system_health()

    render_header(
        title="SIMULATION LAB & GUIDED DEMONSTRATION",
        subtitle="Guided Hackathon Walkthrough, Real-Time Scenario Ingestion & Attack Simulations",
        system_status="ONLINE" if health["database"]["status"] == "ONLINE" else "DEGRADED",
    )

    # Top Control Strip: Reset Simulation Data
    top_c1, top_c2 = st.columns([3, 1])
    with top_c1:
        st.markdown(
            f"""
            <div style="font-size: 0.82rem; color: #D1DDE5;">
                Select a guided demonstration step or individual scenario below to stream transactions into the active pipeline.
                All generated events are cryptographically evaluated with Ed25519, scored by ML models, checked for drift, and persisted to SQLite.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with top_c2:
        if st.button("Reset Simulation Data", key="btn_reset_sim", use_container_width=True):
            dash_service.reset_simulation_data()
            st.success("Simulation tables safely cleared. Keystore and trained models preserved.")
            time.sleep(0.5)
            st.rerun()

    st.markdown("<hr style='border: 1px solid #2A3C48; margin: 0.8rem 0 1.2rem 0;'>", unsafe_allow_html=True)

    # PART D: Guided Hackathon Demonstration Mode
    st.markdown(
        f"""
        <div style="background-color: {CARD_BG}; border: 1px solid {ACCENT_PRIMARY}; border-radius: 8px; padding: 1rem 1.2rem; margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 0.95rem; font-weight: 800; color: #FFFFFF; font-family: 'IBM Plex Mono', monospace;">
                    ★ GUIDED HACKATHON DEMONSTRATION MODE (5-STEP WALKTHROUGH)
                </span>
                <span style="font-size: 0.72rem; font-weight: 700; color: {ACCENT_PRIMARY}; border: 1px solid {ACCENT_PRIMARY}; padding: 0.15rem 0.5rem; border-radius: 4px; font-family: monospace;">
                    EVALUATOR SEQUENCE
                </span>
            </div>
            <div style="font-size: 0.78rem; color: #D1DDE5; margin-bottom: 0.9rem;">
                Follow this sequential sequence during your presentation to visibly demonstrate normal flow, fraud alerts, velocity defense, and cryptographic rejection:
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    demo_steps = [
        {
            "num": "STEP 1",
            "name": "Normal UPI P2M Traffic",
            "desc": "Stream 20 legitimate Swiggy/Zomato/Amazon transfers (₹150-₹2,500).",
            "scenario": ScenarioType.UPI_NORMAL,
            "count": 20,
            "badge": "EXPECT: ALLOW",
            "badge_col": ACCENT_PRIMARY,
        },
        {
            "num": "STEP 2",
            "name": "High-Value Amount Spike",
            "desc": "Inject an astronomical ₹82,500 transfer to an unverified VPA.",
            "scenario": ScenarioType.UPI_AMOUNT_SPIKE,
            "count": 5,
            "badge": "EXPECT: REVIEW / BLOCK",
            "badge_col": COLOR_WARNING,
        },
        {
            "num": "STEP 3",
            "name": "Rapid Velocity Burst",
            "desc": "Burst of 15 payments in seconds to account-draining mule VPA.",
            "scenario": ScenarioType.UPI_VELOCITY_BURST,
            "count": 15,
            "badge": "EXPECT: BLOCK",
            "badge_col": COLOR_CRITICAL,
        },
        {
            "num": "STEP 4",
            "name": "Replay Double-Spend",
            "desc": "Retransmits previously authorized signed payload to double-debit.",
            "scenario": ScenarioType.UPI_REPLAY_ATTACK,
            "count": 10,
            "badge": "EXPECT: REPLAY REJECTED",
            "badge_col": COLOR_CRITICAL,
        },
        {
            "num": "STEP 5",
            "name": "MITM Payload Tampering",
            "desc": "Adversary modifies payment amount in transit without Ed25519 key.",
            "scenario": ScenarioType.UPI_TAMPERED,
            "count": 8,
            "badge": "EXPECT: BAD SIGNATURE REJECTED",
            "badge_col": COLOR_CRITICAL,
        },
    ]

    cols_step = st.columns(5)
    for idx, step in enumerate(demo_steps):
        with cols_step[idx]:
            st.markdown(
                f"""
                <div style="background-color: #192631; border: 1px solid {BORDER_COLOR}; border-radius: 6px; padding: 0.75rem; height: 165px; margin-bottom: 0.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
                        <span style="font-size: 0.7rem; font-weight: 700; color: {ACCENT_PRIMARY}; font-family: monospace;">{step['num']}</span>
                        <span style="font-size: 0.65rem; font-weight: 700; color: {step['badge_col']}; border: 1px solid {step['badge_col']}; padding: 0.1rem 0.3rem; border-radius: 3px;">
                            {step['badge']}
                        </span>
                    </div>
                    <div style="font-size: 0.82rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.3rem;">
                        {step['name']}
                    </div>
                    <div style="font-size: 0.72rem; color: #D1DDE5; line-height: 1.3;">
                        {step['desc']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"▶ Run {step['num']}", key=f"btn_step_{idx}", use_container_width=True):
                with st.spinner(f"Executing {step['name']}..."):
                    controller.step(scenario=step["scenario"], count=step["count"])
                st.toast(f"Executed {step['name']} ({step['count']} events)")
                time.sleep(0.3)
                st.rerun()

    st.markdown("<hr style='border: 1px solid #2A3C48; margin: 1.5rem 0 1.2rem 0;'>", unsafe_allow_html=True)

    # Individual Scenario Selector Grid
    st.markdown(
        f'<div style="font-size: 1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.8rem;">'
        f'Individual Scenario Simulation Sandbox</div>',
        unsafe_allow_html=True,
    )

    scenarios = [
        {
            "id": ScenarioType.UPI_NORMAL,
            "title": "1. UPI Legitimate Baseline",
            "desc": "Standard legitimate UPI transfers with typical amounts, familiar payees, and established devices.",
            "type": "LEGITIMATE",
            "badge_col": ACCENT_PRIMARY,
            "default_count": 25,
        },
        {
            "id": ScenarioType.UPI_AMOUNT_SPIKE,
            "title": "2. High-Value Amount Spike",
            "desc": "Sudden massive transfer (₹65,000 to ₹95,000) breaching standard consumer velocity thresholds.",
            "type": "AMOUNT ANOMALY",
            "badge_col": COLOR_CRITICAL,
            "default_count": 20,
        },
        {
            "id": ScenarioType.UPI_VELOCITY_BURST,
            "title": "3. Rapid Repeated Payments",
            "desc": "High-frequency succession of rapid payments within seconds to the same unverified VPA.",
            "type": "VELOCITY ANOMALY",
            "badge_col": COLOR_WARNING,
            "default_count": 25,
        },
        {
            "id": ScenarioType.UPI_NEW_PAYEE,
            "title": "4. New Payee / Unverified VPA",
            "desc": "Large payment to an unverified, newly created VPA handle with zero prior payment history.",
            "type": "PAYEE ANOMALY",
            "badge_col": COLOR_WARNING,
            "default_count": 20,
        },
        {
            "id": ScenarioType.UPI_DEVICE_CHANGE,
            "title": "5. Untrusted Device / SIM Swap",
            "desc": "Transfer executed on an unrecognized hardware fingerprint mid-session.",
            "type": "DEVICE THREAT",
            "badge_col": COLOR_WARNING,
            "default_count": 20,
        },
        {
            "id": ScenarioType.UPI_LOCATION_JUMP,
            "title": "6. Impossible Location Hop",
            "desc": "Geographical jump to international anonymous VPN/Tor exit nodes minutes after local activity.",
            "type": "NETWORK THREAT",
            "badge_col": COLOR_WARNING,
            "default_count": 20,
        },
        {
            "id": ScenarioType.FRAUD_PATTERN_SHIFT,
            "title": "7. Emerging Fraud Pattern (Drift)",
            "desc": "Concept drift: new emerging fraud modus operandi triggering ADWIN sliding window shift alerts.",
            "type": "CONCEPT DRIFT",
            "badge_col": ACCENT_SECONDARY,
            "default_count": 100,
        },
        {
            "id": ScenarioType.UPI_REPLAY_ATTACK,
            "title": "8. Replay Double-Spend Attack",
            "desc": "Adversary retransmits valid signed authorization payload. Blocked by atomic SQLite replay ledger.",
            "type": "REPLAY ATTACK",
            "badge_col": COLOR_CRITICAL,
            "default_count": 20,
        },
        {
            "id": ScenarioType.UPI_TAMPERED,
            "title": "9. MITM Payload Tampering",
            "desc": "Adversary modifies payment amount or payee in transit without private key. Immediate rejection.",
            "type": "CRYPTOGRAPHIC ATTACK",
            "badge_col": COLOR_CRITICAL,
            "default_count": 15,
        },
        {
            "id": ScenarioType.REAL_DATA_REPLAY,
            "title": "10. Real IEEE-CIS Dataset Replay",
            "desc": "Replays authentic merchant card transactions sampled from the Kaggle IEEE-CIS dataset.",
            "type": "REAL BENCHMARK",
            "badge_col": ACCENT_PRIMARY,
            "default_count": 30,
        },
    ]

    col_grid1, col_grid2 = st.columns(2)

    for idx, sc in enumerate(scenarios):
        target_col = col_grid1 if idx % 2 == 0 else col_grid2

        with target_col:
            st.markdown(
                f"""
                <div style="background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 8px; padding: 1rem 1.15rem; margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                        <span style="font-size: 0.92rem; font-weight: 700; color: #FFFFFF;">
                            {sc['title']}
                        </span>
                        <span style="font-size: 0.68rem; font-weight: 700; color: {sc['badge_col']}; border: 1px solid {sc['badge_col']}; padding: 0.1rem 0.4rem; border-radius: 4px; font-family: 'IBM Plex Mono', monospace;">
                            {sc['type']}
                        </span>
                    </div>
                    <div style="font-size: 0.78rem; color: #D1DDE5; margin-bottom: 0.8rem; height: 38px;">
                        {sc['desc']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Controls inside card
            c_cnt, c_btn = st.columns([1, 1])
            with c_cnt:
                event_count = st.number_input(
                    "Count",
                    min_value=5,
                    max_value=300,
                    value=sc["default_count"],
                    step=5,
                    key=f"cnt_{sc['id'].value}",
                )
            with c_btn:
                st.write("")
                st.write("")
                launch = st.button(
                    f"Run Scenario",
                    key=f"btn_{sc['id'].value}",
                    type="primary" if sc['type'] != "LEGITIMATE" else "secondary",
                    use_container_width=True,
                )

            if launch:
                with st.spinner(f"Executing {sc['title']} with {event_count} events..."):
                    if "upi" in sc["id"].value:
                        summary = controller.step(
                            scenario=sc["id"],
                            count=event_count,
                            anomaly_ratio=0.08 if sc["id"] == ScenarioType.UPI_NORMAL else 0.0,
                        )
                    else:
                        summary = sim_service.execute_scenario(
                            scenario=sc["id"],
                            event_count=event_count,
                            anomaly_ratio=0.08 if sc["id"] == ScenarioType.NORMAL else 0.0,
                        )
                    st.toast(f"Successfully processed {event_count} events")
                    time.sleep(0.4)
                    st.rerun()
