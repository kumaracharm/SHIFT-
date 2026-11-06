"""
DRIFTGUARD Navigation System
Defines sidebar navigation structure, icon mapping, and routing to dashboard pages.
"""

import streamlit as st
from dashboard.theme import (
    ACCENT_PRIMARY,
    ACCENT_SECONDARY,
    BORDER_COLOR,
    BG_SECONDARY,
    TEXT_MUTED,
)

PAGES = [
    "Command Center",
    "Live Transaction Monitor",
    "Fraud Intelligence",
    "Drift Analytics",
    "Event Integrity",
    "Model Laboratory",
    "Simulation Lab",
    "System Settings",
]


def render_sidebar_navigation() -> str:
    """Renders the custom sidebar navigation and returns selected page name."""
    with st.sidebar:
        # Branding Header
        st.markdown(
            f"""
            <div style="padding: 0.5rem 0 1.25rem 0; border-bottom: 1px solid {BORDER_COLOR}; margin-bottom: 1.25rem;">
                <div style="font-size: 1.35rem; font-weight: 800; letter-spacing: -0.02em; color: #FFFFFF;">
                    DRIFT<span style="color: {ACCENT_PRIMARY};">GUARD</span>
                </div>
                <div style="font-size: 0.72rem; color: {TEXT_MUTED}; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 2px;">
                    Streaming Defense Platform
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div style="font-size: 0.72rem; font-weight: 700; color: {TEXT_MUTED}; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;">'
            f'Navigation</div>',
            unsafe_allow_html=True,
        )

        selected_page = st.radio(
            "Navigation Menu",
            PAGES,
            index=0,
            label_visibility="collapsed",
            key="dg_nav_radio",
        )

        st.markdown(
            f"""
            <div style="margin-top: 3rem; padding-top: 1rem; border-top: 1px solid {BORDER_COLOR}; font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; color: {TEXT_MUTED};">
                <div>SYSTEM: <b>SOC ACTIVE</b></div>
                <div>STORAGE: <b>SQLite Persistent</b></div>
                <div>SECURITY: <b>Ed25519 Active</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return selected_page

