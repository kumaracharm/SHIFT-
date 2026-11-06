"""
DRIFTGUARD Dashboard Theme Configuration
Graphite + Arctic Teal Visual Design System for SOC Operations Center.
"""

import plotly.graph_objects as go
import plotly.express as px

# Color Palette
BG_MAIN = "#111A23"
BG_SECONDARY = "#192631"
CARD_BG = "#1E2D39"
BORDER_COLOR = "#2A3C48"
ACCENT_PRIMARY = "#29B6A1"
ACCENT_SECONDARY = "#76CFC0"
COLOR_WARNING = "#E8B45B"
COLOR_CRITICAL = "#E36D63"
COLOR_INFO = "#4DA1A9"
TEXT_MAIN = "#E9EFF3"
TEXT_MUTED = "#9EAFBA"

# Decision Status Badges
DECISION_COLORS = {
    "NORMAL": ACCENT_PRIMARY,
    "MONITOR": ACCENT_SECONDARY,
    "REVIEW": COLOR_WARNING,
    "HIGH_RISK": COLOR_CRITICAL,
    "INTEGRITY_REJECTED": COLOR_CRITICAL,
    "VALID": ACCENT_PRIMARY,
    "STABLE": ACCENT_PRIMARY,
    "DRIFT_DETECTED": COLOR_WARNING,
    "CONCEPT_DRIFT_DETECTED": COLOR_CRITICAL,
}

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: {TEXT_MAIN};
}}

.stApp {{
    background-color: {BG_MAIN};
}}

/* Top Navigation / Header styling */
header[data-testid="stHeader"] {{
    background-color: {BG_MAIN};
    border-bottom: 1px solid {BORDER_COLOR};
}}

/* Sidebar styling */
section[data-testid="stSidebar"] {{
    background-color: {BG_SECONDARY};
    border-right: 1px solid {BORDER_COLOR};
}}

section[data-testid="stSidebar"] div.stRadio > div {{
    gap: 4px;
}}

/* Buttons */
.stButton > button {{
    background-color: {CARD_BG};
    color: {TEXT_MAIN};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    font-weight: 500;
    transition: all 0.2s ease;
    padding: 0.45rem 1rem;
}}

.stButton > button:hover {{
    border-color: {ACCENT_PRIMARY};
    color: {ACCENT_PRIMARY};
    box-shadow: 0 0 10px rgba(41, 182, 161, 0.2);
}}

.stButton > button:active {{
    background-color: rgba(41, 182, 161, 0.15);
}}

/* Primary Action Buttons */
.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, {ACCENT_PRIMARY}, #1f8a7a);
    color: #ffffff;
    border: none;
    font-weight: 600;
}}

.stButton > button[kind="primary"]:hover {{
    background: linear-gradient(135deg, {ACCENT_SECONDARY}, {ACCENT_PRIMARY});
    color: #ffffff;
}}

/* Metric Card Container */
.dg-metric-card {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 1.1rem 1.25rem;
    position: relative;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    margin-bottom: 0.75rem;
}}

.dg-metric-label {{
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: {TEXT_MUTED};
    margin-bottom: 0.35rem;
}}

.dg-metric-value {{
    font-size: 1.85rem;
    font-weight: 700;
    color: {TEXT_MAIN};
    font-family: 'IBM Plex Mono', monospace;
    line-height: 1.2;
}}

.dg-metric-delta {{
    font-size: 0.78rem;
    font-weight: 500;
    margin-top: 0.25rem;
}}

/* Mono Text and Code Elements */
code, pre, .mono {{
    font-family: 'IBM Plex Mono', monospace !important;
}}

/* SOC Status Pills */
.badge {{
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    font-family: 'IBM Plex Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

.badge-normal {{
    background-color: rgba(41, 182, 161, 0.15);
    color: {ACCENT_PRIMARY};
    border: 1px solid rgba(41, 182, 161, 0.4);
}}

.badge-monitor {{
    background-color: rgba(118, 207, 192, 0.15);
    color: {ACCENT_SECONDARY};
    border: 1px solid rgba(118, 207, 192, 0.4);
}}

.badge-review {{
    background-color: rgba(232, 180, 91, 0.15);
    color: {COLOR_WARNING};
    border: 1px solid rgba(232, 180, 91, 0.4);
}}

.badge-critical {{
    background-color: rgba(227, 109, 99, 0.15);
    color: {COLOR_CRITICAL};
    border: 1px solid rgba(227, 109, 99, 0.4);
}}

.badge-rejected {{
    background-color: rgba(227, 109, 99, 0.25);
    color: {COLOR_CRITICAL};
    border: 1px solid {COLOR_CRITICAL};
}}

/* Tables */
div[data-testid="stDataFrame"] {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 0.5rem;
}}

/* Selectbox, TextInput, NumberInput */
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div {{
    background-color: {CARD_BG} !important;
    border-color: {BORDER_COLOR} !important;
    color: {TEXT_MAIN} !important;
    border-radius: 6px !important;
}}

div[data-baseweb="popover"] > div {{
    background-color: {BG_SECONDARY} !important;
    border: 1px solid {BORDER_COLOR} !important;
}}

/* System Status Bar */
.system-status-bar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    background-color: {BG_SECONDARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 0.65rem 1.25rem;
    margin-bottom: 1.25rem;
}}

.status-indicator {{
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 6px;
}}

.indicator-green {{
    background-color: {ACCENT_PRIMARY};
    box-shadow: 0 0 8px {ACCENT_PRIMARY};
}}

.indicator-yellow {{
    background-color: {COLOR_WARNING};
    box-shadow: 0 0 8px {COLOR_WARNING};
}}

.indicator-red {{
    background-color: {COLOR_CRITICAL};
    box-shadow: 0 0 8px {COLOR_CRITICAL};
}}
</style>
"""


def apply_plotly_theme(fig: go.Figure, height: int = 340) -> go.Figure:
    """Applies the Graphite + Arctic Teal theme to any Plotly figure."""
    fig.update_layout(
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        font=dict(
            family="Inter, sans-serif",
            color=TEXT_MAIN,
            size=12,
        ),
        margin=dict(l=40, r=20, t=40, b=40),
        height=height,
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor=BORDER_COLOR,
            borderwidth=1,
            font=dict(size=11, color=TEXT_MUTED),
        ),
        hoverlabel=dict(
            bgcolor=BG_SECONDARY,
            bordercolor=BORDER_COLOR,
            font=dict(family="IBM Plex Mono, monospace", size=12, color=TEXT_MAIN),
        ),
    )
    fig.update_xaxes(
        gridcolor=BORDER_COLOR,
        zerolinecolor=BORDER_COLOR,
        tickfont=dict(color=TEXT_MUTED, size=10),
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikedash="dot",
        spikecolor=ACCENT_PRIMARY,
        spikethickness=1,
    )
    fig.update_yaxes(
        gridcolor=BORDER_COLOR,
        zerolinecolor=BORDER_COLOR,
        tickfont=dict(color=TEXT_MUTED, size=10),
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikedash="dot",
        spikecolor=ACCENT_PRIMARY,
        spikethickness=1,
    )
    return fig

