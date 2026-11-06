"""
DRIFTGUARD Experiments History Page
Audits past simulation runs, benchmarks execution duration, throughput, and decision outcomes.
"""

import json
import streamlit as st
import pandas as pd
import plotly.express as px
from dashboard.components.header import render_header
from dashboard.services.dashboard_service import DashboardService
from dashboard.theme import (
    apply_plotly_theme,
    CARD_BG,
    BORDER_COLOR,
    ACCENT_PRIMARY,
    ACCENT_SECONDARY,
    COLOR_WARNING,
    COLOR_CRITICAL,
    TEXT_MAIN,
    TEXT_MUTED,
)


def render_experiments_page():
    service = DashboardService()
    health = service.get_system_health()
    runs_df = service.get_experiment_runs(limit=50)

    render_header(
        title="EXPERIMENT HISTORY & BENCHMARKS",
        subtitle="Historical Simulation Audits, Throughput Telemetry & Replay Experiment Runs",
        system_status="ONLINE" if health["database"]["status"] == "ONLINE" else "DEGRADED",
    )

    if runs_df.empty:
        st.info("No experiment runs recorded in SQLite database yet. Execute scenarios in the Simulation Lab to build history.")
        return

    # Benchmark Throughput Chart across runs
    st.markdown(
        f'<div style="font-size: 1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.4rem;">'
        f'Scenario Processing Duration & Volume Benchmarks</div>',
        unsafe_allow_html=True,
    )

    fig = px.bar(
        runs_df,
        x="run_id",
        y="total_events",
        color="scenario_name",
        title="Event Volume by Historical Run",
        labels={"run_id": "Experiment Run ID", "total_events": "Total Events Processed", "scenario_name": "Scenario"},
        color_discrete_sequence=[ACCENT_PRIMARY, ACCENT_SECONDARY, COLOR_WARNING, COLOR_CRITICAL, "#4DA1A9"],
    )
    st.plotly_chart(apply_plotly_theme(fig, height=270), use_container_width=True)

    # Experiments Table
    st.markdown(
        f'<div style="font-size: 1rem; font-weight: 700; color: #FFFFFF; margin-top: 1rem; margin-bottom: 0.4rem;">'
        f'Experiment Records ({len(runs_df)} Recorded Runs)</div>',
        unsafe_allow_html=True,
    )

    disp = runs_df[["run_id", "scenario_name", "start_time", "total_events", "rejected_events", "flagged_events", "duration_seconds"]].copy()
    disp["start_time"] = pd.to_datetime(disp["start_time"]).dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    disp["duration_seconds"] = disp["duration_seconds"].apply(lambda s: f"{s:.2f}s")
    disp = disp.rename(columns={
        "run_id": "Experiment ID",
        "scenario_name": "Scenario",
        "start_time": "Executed At",
        "total_events": "Events",
        "rejected_events": "Rejected (Sec)",
        "flagged_events": "Flagged (Fraud)",
        "duration_seconds": "Duration",
    })
    st.dataframe(disp, use_container_width=True, height=280, hide_index=True)

    # Detail View of Selected Experiment
    run_ids = runs_df["run_id"].tolist()
    if run_ids:
        sel_run = st.selectbox("Select Experiment Run to View Telemetry Summary", run_ids, key="exp_sel_run")
        run_record = runs_df[runs_df["run_id"] == sel_run].iloc[0]
        st.markdown(
            f"""
            <div style="background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 6px; padding: 1rem; font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem;">
                <div style="color: {ACCENT_PRIMARY}; font-weight: 700; margin-bottom: 0.4rem;">EXPERIMENT: {run_record['run_id']}</div>
                <div><b>SCENARIO:</b> {run_record['scenario_name']}</div>
                <div><b>TOTAL EVENTS:</b> {run_record['total_events']}</div>
                <div><b>REJECTED EVENTS:</b> {run_record['rejected_events']}</div>
                <div><b>FLAGGED FRAUD:</b> {run_record['flagged_events']}</div>
                <div><b>EXECUTION TIME:</b> {run_record['duration_seconds']}</div>
                <div style="margin-top: 0.5rem; word-break: break-all; color: #D1DDE5;">
                    <b>SUMMARY JSON:</b> {json.dumps(run_record['summary'], indent=2)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

