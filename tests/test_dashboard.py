"""
DRIFTGUARD Dashboard & Service Layer Tests
Verifies dashboard data aggregation, real SQLite querying, simulation triggers, and safe resets.
"""

import pytest
from storage.database import SessionLocal, init_db, engine
from dashboard.services.dashboard_service import DashboardService
from dashboard.services.simulation_service import SimulationService
from simulation.scenarios import ScenarioType


@pytest.fixture(scope="module")
def setup_database():
    init_db(engine)
    yield


def test_dashboard_service_kpis(setup_database):
    service = DashboardService()
    kpis = service.get_kpis()

    assert "total_events" in kpis
    assert "trusted_events" in kpis
    assert "rejected_events" in kpis
    assert "high_risk" in kpis
    assert "review" in kpis
    assert "monitor" in kpis
    assert "normal" in kpis
    assert "drift_alerts" in kpis
    assert "active_model_id" in kpis


def test_dashboard_service_queries(setup_database):
    service = DashboardService()
    tx_df = service.get_recent_transactions(limit=10)
    assert tx_df is not None

    logs_df = service.get_integrity_logs(limit=10)
    assert logs_df is not None

    drift_df = service.get_drift_events(limit=10)
    assert drift_df is not None

    exp_df = service.get_experiment_runs(limit=10)
    assert exp_df is not None

    health = service.get_system_health()
    assert health["database"]["status"] == "ONLINE"
    assert health["security"]["status"] == "ACTIVE"


def test_simulation_service_execution(setup_database):
    sim_service = SimulationService()
    summary = sim_service.execute_scenario(ScenarioType.NORMAL, event_count=10)

    assert summary["scenario"] == "normal"
    assert summary["total_events"] == 10
    assert "decision_breakdown" in summary
    assert summary["duration_seconds"] >= 0.0

    # Also test REAL_DATA_REPLAY scenario execution
    real_summary = sim_service.execute_scenario(ScenarioType.REAL_DATA_REPLAY, event_count=5)
    assert real_summary["scenario"] == "real_data_replay"
    assert real_summary["total_events"] == 5


def test_reset_simulation_data(setup_database):
    service = DashboardService()
    # Execute a small run
    sim_service = SimulationService()
    sim_service.execute_scenario(ScenarioType.NORMAL, event_count=5)

    # Now reset
    service.reset_simulation_data()
    kpis = service.get_kpis()
    assert kpis["total_events"] == 0
    assert kpis["rejected_events"] == 0

