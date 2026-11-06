"""
DRIFTGUARD Dashboard Header Component
Branding, live operational health indicators, and global refresh controls.
"""

from datetime import datetime, timezone
import streamlit as st
from dashboard.theme import (
    ACCENT_PRIMARY,
    TEXT_MUTED,
    BORDER_COLOR,
    CARD_BG,
    BG_SECONDARY,
)


def render_header(
    title: str = "SECURITY OPERATIONS CENTER",
    subtitle: str = "Adaptive Streaming Fraud & Threat Detection Engine",
    system_status: str = "ONLINE",
):
    """Renders the top branding and operational status banner."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    indicator_class = "indicator-green" if system_status == "ONLINE" else "indicator-yellow"

    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; 
                    padding: 0.85rem 1.25rem; background-color: {BG_SECONDARY}; 
                    border: 1px solid {BORDER_COLOR}; border-radius: 8px; margin-bottom: 1.25rem;">
            <div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.4rem; font-weight: 800; letter-spacing: -0.02em; color: #FFFFFF;">
                        DRIFT<span style="color: {ACCENT_PRIMARY};">GUARD</span>
                    </span>
                    <span style="font-size: 0.75rem; background-color: rgba(41, 182, 161, 0.15); 
                                 color: {ACCENT_PRIMARY}; padding: 0.15rem 0.5rem; border-radius: 4px; 
                                 font-weight: 600; font-family: 'IBM Plex Mono', monospace;">
                        v1.2-SOC
                    </span>
                    <span style="color: {BORDER_COLOR};">|</span>
                    <span style="font-size: 0.95rem; font-weight: 600; color: #E9EFF3;">
                        {title}
                    </span>
                </div>
                <div style="font-size: 0.78rem; color: {TEXT_MUTED}; margin-top: 2px;">
                    {subtitle}
                </div>
            </div>
            <div style="text-align: right; display: flex; align-items: center; gap: 18px;">
                <div style="text-align: right;">
                    <div style="display: flex; align-items: center; justify-content: flex-end;">
                        <span class="status-indicator {indicator_class}"></span>
                        <span style="font-size: 0.8rem; font-weight: 600; font-family: 'IBM Plex Mono', monospace; color: {ACCENT_PRIMARY};">
                            {system_status}
                        </span>
                    </div>
                    <div style="font-size: 0.72rem; color: {TEXT_MUTED}; font-family: 'IBM Plex Mono', monospace;">
                        {now_str}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

