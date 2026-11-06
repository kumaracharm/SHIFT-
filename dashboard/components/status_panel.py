"""
DRIFTGUARD System Status Panel Component
Provides visual verification of storage, cryptographic keystore, models, and drift health.
"""

from typing import Dict, Any
import streamlit as st
from dashboard.theme import (
    CARD_BG,
    BORDER_COLOR,
    ACCENT_PRIMARY,
    COLOR_WARNING,
    COLOR_CRITICAL,
    TEXT_MUTED,
)


def render_system_health_panel(health: Dict[str, Any]):
    """Renders a 4-card operational readiness indicator row."""
    st.markdown(
        f'<div style="font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: {TEXT_MUTED}; margin-bottom: 0.6rem;">Operational Engine Health</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    modules = [
        ("Storage Engine", health.get("database", {}), c1),
        ("Ed25519 Boundary", health.get("security", {}), c2),
        ("Inference Engine", health.get("model", {}), c3),
        ("Drift Telemetry", health.get("drift_detector", {}), c4),
    ]

    for title, info, col in modules:
        status = info.get("status", "UNKNOWN")
        detail = info.get("detail", "")

        if status in ("ONLINE", "ACTIVE", "LOADED"):
            status_color = ACCENT_PRIMARY
            dot_class = "indicator-green"
        elif status in ("UNFITTED", "DEGRADED"):
            status_color = COLOR_WARNING
            dot_class = "indicator-yellow"
        else:
            status_color = COLOR_CRITICAL
            dot_class = "indicator-red"

        with col:
            st.markdown(
                f"""
                <div style="background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; 
                            border-radius: 6px; padding: 0.75rem 0.9rem; margin-bottom: 0.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
                        <span style="font-size: 0.75rem; font-weight: 600; color: #FFFFFF;">
                            {title}
                        </span>
                        <span style="display: flex; align-items: center; font-size: 0.7rem; font-weight: 700; color: {status_color}; font-family: 'IBM Plex Mono', monospace;">
                            <span class="status-indicator {dot_class}"></span>{status}
                        </span>
                    </div>
                    <div style="font-size: 0.72rem; color: {TEXT_MUTED}; font-family: 'IBM Plex Mono', monospace; 
                                overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        {detail}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

