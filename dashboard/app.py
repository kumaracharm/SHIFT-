"""
DRIFTGUARD Streamlit Application Entrypoint
Security Operations Center (SOC) Adaptive Streaming Fraud & Threat Detection Dashboard.
"""

import sys
from pathlib import Path

# Ensure root directory is on pythonpath for seamless imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from dashboard.theme import CUSTOM_CSS
from dashboard.navigation import render_sidebar_navigation
from dashboard.pages.overview import render_overview_page
from dashboard.pages.live_monitoring import render_live_monitoring_page
from dashboard.pages.fraud_intelligence import render_fraud_intelligence_page
from dashboard.pages.drift_analytics import render_drift_analytics_page
from dashboard.pages.event_integrity import render_event_integrity_page
from dashboard.pages.model_laboratory import render_model_laboratory_page
from dashboard.pages.simulation_lab import render_simulation_lab_page
from dashboard.pages.experiments import render_experiments_page
from dashboard.pages.settings import render_settings_page

# Set Page Configuration
st.set_page_config(
    page_title="DRIFTGUARD — Adaptive Fraud & Threat Defense SOC",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject Custom Graphite + Arctic Teal CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def main():
    selected_page = render_sidebar_navigation()

    page_router = {
        "Command Center": render_overview_page,
        "Live Transaction Monitor": render_live_monitoring_page,
        "Fraud Intelligence": render_fraud_intelligence_page,
        "Drift Analytics": render_drift_analytics_page,
        "Event Integrity": render_event_integrity_page,
        "Model Laboratory": render_model_laboratory_page,
        "Simulation Lab": render_simulation_lab_page,
        "System Settings": render_settings_page,
    }

    render_fn = page_router.get(selected_page, render_overview_page)
    render_fn()


if __name__ == "__main__":
    main()

