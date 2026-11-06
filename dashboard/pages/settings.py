"""
DRIFTGUARD Settings & System Configuration Page
Displays active environment parameters, cryptographic thresholds, and technical roadmap.
"""

import streamlit as st
from config import settings
from dashboard.components.header import render_header
from dashboard.services.dashboard_service import DashboardService
from dashboard.theme import (
    CARD_BG,
    BORDER_COLOR,
    ACCENT_PRIMARY,
    ACCENT_SECONDARY,
    COLOR_WARNING,
    TEXT_MAIN,
    TEXT_MUTED,
)


def render_settings_page():
    service = DashboardService()
    health = service.get_system_health()

    render_header(
        title="SYSTEM SETTINGS & ARCHITECTURE",
        subtitle="Global Detection Thresholds, Cryptographic Parameters & Module Configuration",
        system_status="ONLINE" if health["database"]["status"] == "ONLINE" else "DEGRADED",
    )

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            f"""
            <div style="background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 8px; padding: 1.15rem; margin-bottom: 1rem;">
                <div style="font-size: 0.85rem; font-weight: 700; color: {ACCENT_PRIMARY}; margin-bottom: 0.5rem; text-transform: uppercase;">
                    Decision Engine Thresholds
                </div>
                <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; line-height: 1.6; color: #D1DDE5;">
                    • <b>HIGH RISK PROBABILITY:</b> {settings.THRESHOLD_HIGH_RISK:.2f} (≥ 75%)<br>
                    • <b>REVIEW PROBABILITY:</b> {settings.THRESHOLD_REVIEW:.2f} (≥ 40%)<br>
                    • <b>MONITOR PROBABILITY:</b> {settings.THRESHOLD_MONITOR:.2f} (≥ 20%)<br>
                    • <b>HST ANOMALY THRESHOLD:</b> {settings.HST_ANOMALY_THRESHOLD:.2f}<br>
                    • <b>AMOUNT Z-SCORE ALERT:</b> {settings.AMOUNT_ZSCORE_WARNING:.1f}σ<br>
                    • <b>VELOCITY WARNING COUNT:</b> {settings.VELOCITY_WARNING_COUNT} events / 60s
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div style="background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 8px; padding: 1.15rem; margin-bottom: 1rem;">
                <div style="font-size: 0.85rem; font-weight: 700; color: {ACCENT_SECONDARY}; margin-bottom: 0.5rem; text-transform: uppercase;">
                    Cryptographic Security Parameters
                </div>
                <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; line-height: 1.6; color: #D1DDE5;">
                    • <b>ALGORITHM:</b> Ed25519 (Elliptic Curve Digital Signature)<br>
                    • <b>CANONICAL SERIALIZATION:</b> Deterministic JSON Bytes (RFC-8785 conformant)<br>
                    • <b>PRIMARY KEY ID:</b> {settings.DEFAULT_KEY_ID}<br>
                    • <b>FRESHNESS WINDOW:</b> {settings.MAX_EVENT_AGE_SECONDS} seconds (5 minutes)<br>
                    • <b>CLOCK SKEW ALLOWANCE:</b> {settings.MAX_CLOCK_SKEW_SECONDS} seconds<br>
                    • <b>REPLAY LEDGER:</b> Atomic SQLite Unique (Key ID, Nonce) & Event ID
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div style="background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 8px; padding: 1.15rem; margin-bottom: 1rem;">
                <div style="font-size: 0.85rem; font-weight: 700; color: {COLOR_WARNING}; margin-bottom: 0.5rem; text-transform: uppercase;">
                    Storage & Pipeline Architecture
                </div>
                <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; line-height: 1.6; color: #D1DDE5;">
                    • <b>PERSISTENCE ENGINE:</b> SQLite Local Monolith (SQLAlchemy ORM)<br>
                    • <b>DATABASE FILE:</b> ./driftguard.db<br>
                    • <b>KEYSTORE:</b> ./keys/ (Ed25519 PEM Asymmetric Keypairs)<br>
                    • <b>MODEL ARTIFACTS:</b> ./saved_models/ (*.joblib)<br>
                    • <b>DATA INGESTION:</b> ./data/raw/ieee_cis/ & ./data/simulated/<br>
                    • <b>MAX TRANSACTION RATE:</b> 10 events / second (CPU bounded)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div style="background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 8px; padding: 1.15rem; margin-bottom: 1rem;">
                <div style="font-size: 0.85rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.5rem; text-transform: uppercase;">
                    System Status & Roadmap
                </div>
                <div style="font-size: 0.78rem; color: #D1DDE5; line-height: 1.5;">
                    <b>Phase 1 Backend:</b> COMPLETE (Engine, Streaming, Security, SQLite)<br>
                    <b>Phase 2 Dashboard:</b> COMPLETE (Streamlit SOC, Interactive Simulation Lab)<br>
                    <b>Phase 3 Planned:</b> Multi-agent investigator copilot, distributed Redis stream cluster, hardware HSM key integration.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

