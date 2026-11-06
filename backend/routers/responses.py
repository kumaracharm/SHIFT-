"""
DRIFTGUARD 2.0 Adaptive Response Centre Router
"""

from fastapi import APIRouter, Body
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dashboard.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/v1/responses", tags=["Responses"])

# In-memory entity watchlist / remediation rule store
WATCHLIST_STORE: List[Dict[str, Any]] = [
    {"entity_id": "MERCHANT_MULE_01", "type": "BLOCKLIST", "reason": "Confirmed UPI mule aggregation node", "added_at": "2026-11-06T10:00:00Z"},
    {"entity_id": "USER_VIP_9912", "type": "ALLOWLIST", "reason": "Verified enterprise corporate treasury account", "added_at": "2026-11-06T10:05:00Z"},
]

DEFAULT_POLICIES = [
    {
        "id": "POL-01",
        "name": "Zero-Trust Cryptographic Enforcement",
        "description": "Immediately terminate and reject transactions with invalid Ed25519 signature, timestamp expiration (>120s), or reused nonce.",
        "action": "BLOCK",
        "status": "ENFORCED",
        "priority": "CRITICAL",
    },
    {
        "id": "POL-02",
        "name": "Supervised High-Confidence Fraud Containment",
        "description": "Block transactions where supervised model probability exceeds 0.70 or context risk >= 0.80.",
        "action": "BLOCK",
        "status": "ENFORCED",
        "priority": "HIGH",
    },
    {
        "id": "POL-03",
        "name": "Adaptive Step-Up Authentication",
        "description": "Route transactions with elevated anomaly score (>= 0.65) or velocity bursts to manual review and biometric OTP challenge.",
        "action": "REVIEW",
        "status": "ENFORCED",
        "priority": "MEDIUM",
    },
    {
        "id": "POL-04",
        "name": "High-Value Transfer Velocity Brake",
        "description": "Enforce review on UPI transfers exceeding ₹50,000 occurring within 5 seconds of previous debit.",
        "action": "REVIEW",
        "status": "ENFORCED",
        "priority": "HIGH",
    },
]


@router.get("/policies")
def list_policies() -> Dict[str, Any]:
    """Retrieves current active automated remediation policies."""
    return {
        "status": "success",
        "policies": DEFAULT_POLICIES,
    }


@router.get("/actions")
def get_actions_summary() -> Dict[str, Any]:
    """Retrieves execution metrics of recent automated responses."""
    dash_service = DashboardService()
    kpis = dash_service.get_kpis()

    return {
        "status": "success",
        "summary": {
            "total_evaluated": kpis.get("total_events", 0),
            "allowed_auto": kpis.get("allow", 0),
            "routed_to_review": kpis.get("action_review", 0),
            "blocked_auto": kpis.get("block", 0),
            "remediation_rate": round(
                ((kpis.get("block", 0) + kpis.get("action_review", 0)) / max(1, kpis.get("total_events", 1))) * 100,
                2,
            ),
        },
    }


@router.post("/simulate")
def simulate_policy_adjustment(
    threshold_block: float = Body(0.65, embed=True),
    threshold_review: float = Body(0.35, embed=True),
) -> Dict[str, Any]:
    """
    Simulates impact of modifying risk thresholds against the historical dataset.
    Returns projected changes in Block, Review, and Allow volumes without affecting live production.
    """
    dash_service = DashboardService()
    df = dash_service.get_recent_transactions(limit=200)

    if df.empty:
        return {"status": "success", "simulation": {"allow": 0, "review": 0, "block": 0, "total": 0}}

    total = len(df)
    sim_blocks = 0
    sim_reviews = 0
    sim_allows = 0

    for _, r in df.iterrows():
        prob = float(r.get("fraud_probability", 0.0))
        anom = float(r.get("anomaly_score", 0.0))
        composite = max(prob, anom * 0.8)

        if r.get("integrity_status") != "VALID" or composite >= threshold_block:
            sim_blocks += 1
        elif composite >= threshold_review:
            sim_reviews += 1
        else:
            sim_allows += 1

    return {
        "status": "success",
        "simulation": {
            "threshold_block": threshold_block,
            "threshold_review": threshold_review,
            "total_tested": total,
            "projected_allow": sim_allows,
            "projected_review": sim_reviews,
            "projected_block": sim_blocks,
            "allow_percentage": round((sim_allows / total) * 100, 1) if total else 0,
            "review_percentage": round((sim_reviews / total) * 100, 1) if total else 0,
            "block_percentage": round((sim_blocks / total) * 100, 1) if total else 0,
        },
    }


@router.get("/watchlist")
def get_watchlist() -> Dict[str, Any]:
    """Retrieves active entity allowlist and blocklist entries."""
    return {
        "status": "success",
        "watchlist": WATCHLIST_STORE,
    }


@router.post("/watchlist")
def add_to_watchlist(
    entity_id: str = Body(..., embed=True),
    type: str = Body("BLOCKLIST", embed=True),  # ALLOWLIST or BLOCKLIST
    reason: str = Body("", embed=True),
) -> Dict[str, Any]:
    """Appends an entity to the simulated allowlist or blocklist."""
    entry = {
        "entity_id": entity_id,
        "type": type.upper(),
        "reason": reason,
        "added_at": datetime.now(timezone.utc).isoformat(),
    }
    WATCHLIST_STORE.append(entry)
    return {
        "status": "success",
        "message": f"Entity '{entity_id}' added to {type.upper()}",
        "entry": entry,
    }

