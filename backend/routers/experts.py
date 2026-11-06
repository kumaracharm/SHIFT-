"""
DRIFTGUARD 2.0 Multi-Expert Detection Router
"""

from fastapi import APIRouter, Body
from typing import Dict, Any, List
from engine.risk_fusion import RiskFusionEngine

router = APIRouter(prefix="/api/v1/experts", tags=["Experts"])

# Shared singleton for dynamic weight adjustments across the application session
SHARED_FUSION_ENGINE = RiskFusionEngine()


@router.get("/status")
def get_experts_status() -> Dict[str, Any]:
    """Retrieves operational status, architecture, and sensitivity weights of the 7 experts."""
    configs = SHARED_FUSION_ENGINE.get_expert_configs()
    total_weight = sum(c["weight"] for c in configs)

    for c in configs:
        c["status"] = "ACTIVE"
        c["weight_percent"] = round((c["weight"] / total_weight) * 100, 1)

    return {
        "status": "success",
        "total_experts": len(configs),
        "total_weight": round(total_weight, 2),
        "experts": configs,
    }


@router.post("/weights")
def update_expert_weights(
    weights: Dict[str, float] = Body(...),
) -> Dict[str, Any]:
    """Dynamically calibrates sensitivity weights for the 7 detection experts."""
    SHARED_FUSION_ENGINE.set_expert_weights(weights)
    return {
        "status": "success",
        "message": "Expert weights recalibrated successfully",
        "current_weights": {e.name: e.weight for e in SHARED_FUSION_ENGINE.experts},
    }


@router.post("/evaluate")
def evaluate_transaction_payload(
    payload: Dict[str, Any] = Body(...),
) -> Dict[str, Any]:
    """Executes ad-hoc multi-expert evaluation and returns the complete transparent fusion breakdown."""
    features = payload.get("features", {})
    if not features:
        features = {
            "amount": float(payload.get("amount", 100.0)),
            "log_amount": 5.0,
            "amount_zscore": 0.5,
            "time_since_prev": 30.0,
            "transaction_velocity": 1.0,
            "device_consistency": 1.0,
            "session_consistency": 1.0,
            "network_risk_flag": 0.0,
        }

    evaluation = SHARED_FUSION_ENGINE.evaluate(
        event_dict=payload,
        features_dict=features,
    )

    return {
        "status": "success",
        "data": evaluation,
    }
