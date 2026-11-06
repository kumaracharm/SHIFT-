"""
Tests for DRIFTGUARD 2.0 Backend REST API handlers and business logic.
Tests all 10 module handlers directly for robust verification.
"""

import pytest
import asyncio
from backend.main import read_root
from backend.routers.overview import get_overview_summary, get_overview_trends, get_recent_alerts
from backend.routers.transactions import list_transactions, get_transaction_detail
from backend.routers.investigations import list_investigation_cases, update_case_action
from backend.routers.entities import get_entity_graph, get_entity_profile
from backend.routers.experts import get_experts_status, update_expert_weights, evaluate_transaction_payload
from backend.routers.responses import list_policies, get_actions_summary, simulate_policy_adjustment, get_watchlist, add_to_watchlist
from backend.routers.models import get_active_model, get_benchmark_provenance, list_model_history
from backend.routers.drift import get_drift_summary, get_feature_drift_breakdown, list_drift_events
from backend.routers.simulation import get_simulation_state, list_available_scenarios, step_simulation
from backend.routers.system import get_system_health, get_key_status, get_db_stats


def test_root():
    res = read_root()
    assert res["platform"] == "DRIFTGUARD 2.0"
    assert res["status"] == "online"


def test_overview():
    summary = get_overview_summary()
    assert summary["status"] == "success"
    assert "total_events" in summary["data"]

    trends = get_overview_trends()
    assert trends["status"] == "success"
    assert "timestamps" in trends["data"]

    alerts = get_recent_alerts(limit=5)
    assert alerts["status"] == "success"
    assert isinstance(alerts["data"], list)


def test_transactions():
    txs = list_transactions(limit=10, offset=0)
    assert txs["status"] == "success"
    assert "data" in txs
    if txs["data"]:
        sample_id = txs["data"][0]["event_id"]
        detail = get_transaction_detail(sample_id)
        assert detail["status"] == "success"
        assert detail["data"]["event_id"] == sample_id


def test_investigations():
    cases = list_investigation_cases(limit=10)
    assert cases["status"] == "success"
    assert "cases" in cases

    # Update action
    act = update_case_action(event_id="test-event-01", action="ESCALATE", notes="Flagged during automated test")
    assert act["status"] == "success"
    assert act["data"]["status"] == "ESCALATE"


def test_entities():
    graph = get_entity_graph(limit=15)
    assert graph["status"] == "success"
    assert len(graph["categories"]) == 5
    assert isinstance(graph["nodes"], list)
    assert isinstance(graph["links"], list)

    profile = get_entity_profile("USER_TEST")
    assert profile["status"] == "success"
    assert "risk_rating" in profile


def test_experts():
    status = get_experts_status()
    assert status["status"] == "success"
    assert status["total_experts"] == 7

    weights = update_expert_weights({"Supervised Fraud Expert": 2.2})
    assert weights["status"] == "success"

    eval_res = evaluate_transaction_payload({
        "amount": 25000.0,
        "features": {
            "amount": 25000.0,
            "log_amount": 10.1,
            "amount_zscore": 2.0,
            "time_since_prev": 15.0,
            "transaction_velocity": 2.0,
            "device_consistency": 0.9,
            "session_consistency": 0.9,
            "network_risk_flag": 0.0,
        },
    })
    assert eval_res["status"] == "success"
    assert "fused_risk_score" in eval_res["data"]
    assert len(eval_res["data"]["expert_breakdown"]) == 7


def test_responses():
    policies = list_policies()
    assert len(policies["policies"]) >= 4

    summary = get_actions_summary()
    assert "remediation_rate" in summary["summary"]

    sim = simulate_policy_adjustment(threshold_block=0.75, threshold_review=0.45)
    assert sim["status"] == "success"
    assert "projected_block" in sim["simulation"]

    wl = get_watchlist()
    assert len(wl["watchlist"]) >= 2


def test_models():
    active = get_active_model()
    assert active["status"] == "success"
    assert "rf_" in active["active_model"]["version_id"]

    bench = get_benchmark_provenance()
    assert bench["status"] == "success"
    assert bench["benchmark"]["metrics"]["roc_auc"] == 0.8954
    assert len(bench["feature_importances"]) >= 5


def test_drift():
    sum_drift = get_drift_summary()
    assert sum_drift["status"] == "success"
    assert "adwin_unlabelled" in sum_drift

    feat_drift = get_feature_drift_breakdown()
    assert feat_drift["status"] == "success"
    assert len(feat_drift["features"]) >= 4

    events = list_drift_events(limit=5)
    assert events["status"] == "success"


def test_simulation_step():
    state = get_simulation_state()
    assert state["status"] == "success"

    scenarios = list_available_scenarios()
    assert scenarios["total"] >= 10

    # Test step execution
    res = step_simulation(count=2, scenario="upi_normal")
    assert res["status"] == "success"
    assert res["count"] == 2


def test_system():
    health = get_system_health()
    assert health["status"] == "healthy"
    assert health["database_connected"] is True
    assert health["cryptographic_key_loaded"] is True

    keys = get_key_status()
    assert keys["algorithm"] == "Ed25519 (RFC 8032)"
    assert keys["public_key_present"] is True

    stats = get_db_stats()
    assert stats["status"] == "success"
    assert stats["size_mb"] > 0
