"""
Tests for DRIFTGUARD 2.0 Multi-Expert Detection Architecture and Risk Fusion.
"""

import pytest
from models.experts.specialists import (
    SupervisedFraudExpert,
    BehaviouralAnomalyExpert,
    IsolationForestExpert,
    TransactionVelocityExpert,
    DeviceSessionExpert,
    NetworkRiskExpert,
    RuleExpert,
)
from engine.risk_fusion import RiskFusionEngine


def test_individual_experts_evaluate():
    event_dict = {
        "amount": 150000.0,
        "payload_json": {"receiver_id": "MULE_RING_01"},
    }
    features_dict = {
        "amount": 150000.0,
        "log_amount": 11.9,
        "amount_zscore": 5.2,
        "time_since_prev": 1.0,
        "transaction_velocity": 7.0,
        "device_consistency": 0.2,
        "session_consistency": 0.3,
        "network_risk_flag": 1.0,
    }

    # Velocity Expert
    v_expert = TransactionVelocityExpert()
    v_res = v_expert.evaluate(event_dict, features_dict)
    assert v_res.score > 0.7
    assert v_res.decision == "BLOCK"

    # Device Expert
    d_expert = DeviceSessionExpert()
    d_res = d_expert.evaluate(event_dict, features_dict)
    assert d_res.score > 0.7
    assert d_res.decision == "BLOCK"

    # Network Expert
    n_expert = NetworkRiskExpert()
    n_res = n_expert.evaluate(event_dict, features_dict)
    assert n_res.score >= 0.85
    assert n_res.decision == "BLOCK"

    # Rule Expert
    r_expert = RuleExpert()
    r_res = r_expert.evaluate(event_dict, features_dict)
    assert r_res.score >= 0.90
    assert r_res.decision == "BLOCK"


def test_risk_fusion_consensus():
    rf = RiskFusionEngine()

    # High risk case
    high_risk_event = {"amount": 250000.0}
    high_risk_feats = {
        "amount": 250000.0,
        "log_amount": 12.4,
        "amount_zscore": 6.0,
        "time_since_prev": 0.5,
        "transaction_velocity": 8.0,
        "device_consistency": 0.1,
        "session_consistency": 0.2,
        "network_risk_flag": 1.0,
    }
    res_high = rf.evaluate(high_risk_event, high_risk_feats)
    assert res_high["fused_risk_score"] > 0.50
    assert res_high["consensus_action"] == "BLOCK"
    assert len(res_high["expert_breakdown"]) == 7
    assert len(res_high["top_contributors"]) >= 1

    # Normal low risk case
    norm_event = {"amount": 350.0}
    norm_feats = {
        "amount": 350.0,
        "log_amount": 5.8,
        "amount_zscore": 0.1,
        "time_since_prev": 120.0,
        "transaction_velocity": 1.0,
        "device_consistency": 0.98,
        "session_consistency": 0.99,
        "network_risk_flag": 0.0,
    }
    res_norm = rf.evaluate(norm_event, norm_feats)
    assert res_norm["fused_risk_score"] < 0.35
    assert res_norm["consensus_action"] == "ALLOW"
    assert res_norm["votes"]["ALLOW"] >= 5
