"""
DRIFTGUARD KPI Cards Component
Renders dense, high-impact metric cards with real backend numbers.
"""

from typing import Dict, Any
import streamlit as st
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


def render_kpi_card(
    label: str,
    value: Any,
    subtext: str = "",
    value_color: str = TEXT_MAIN,
    border_accent: str = BORDER_COLOR,
):
    """Renders a single styled metric card."""
    st.markdown(
        f"""
        <div style="background-color: {CARD_BG}; border: 1px solid {border_accent}; 
                    border-radius: 8px; padding: 1rem 1.15rem; margin-bottom: 0.8rem;
                    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);">
            <div style="font-size: 0.72rem; font-weight: 600; text-transform: uppercase; 
                        letter-spacing: 0.06em; color: {TEXT_MUTED}; margin-bottom: 0.25rem;">
                {label}
            </div>
            <div style="font-size: 1.85rem; font-weight: 700; color: {value_color}; 
                        font-family: 'IBM Plex Mono', monospace; line-height: 1.15;">
                {value}
            </div>
            <div style="font-size: 0.75rem; color: {TEXT_MUTED}; margin-top: 0.35rem; font-family: 'IBM Plex Mono', monospace;">
                {subtext}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_row(kpis: Dict[str, Any]):
    """Renders a 6-column KPI summary row."""
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    total_events = kpis.get("total_events", 0)
    trusted_events = kpis.get("trusted_events", 0)
    rejected_events = kpis.get("rejected_events", 0)
    high_risk = kpis.get("high_risk", 0)
    review = kpis.get("review", 0)
    drift_alerts = kpis.get("drift_alerts", 0)

    # Acceptance rate
    accept_rate = (trusted_events / max(1, (trusted_events + rejected_events))) * 100

    with col1:
        render_kpi_card("Total Ingested", f"{total_events:,}", "Streaming throughput", TEXT_MAIN)
    with col2:
        render_kpi_card("Trusted (Valid)", f"{trusted_events:,}", f"{accept_rate:.1f}% integrity rate", ACCENT_PRIMARY, ACCENT_PRIMARY)
    with col3:
        rej_color = COLOR_CRITICAL if rejected_events > 0 else TEXT_MUTED
        render_kpi_card("Rejected Attacks", f"{rejected_events:,}", "Tampered / Replayed", rej_color, rej_color if rejected_events > 0 else BORDER_COLOR)
    with col4:
        hr_color = COLOR_CRITICAL if high_risk > 0 else TEXT_MAIN
        render_kpi_card("High Risk Fraud", f"{high_risk:,}", "Immediate block/alert", hr_color, hr_color if high_risk > 0 else BORDER_COLOR)
    with col5:
        rev_color = COLOR_WARNING if review > 0 else TEXT_MAIN
        render_kpi_card("Manual Review", f"{review:,}", "Supervised escalation", rev_color)
    with col6:
        drift_color = COLOR_WARNING if drift_alerts > 0 else ACCENT_SECONDARY
        render_kpi_card("Drift Alerts", f"{drift_alerts:,}", "ADWIN / PSI shifts", drift_color)

