"""
DRIFTGUARD 2.0 Fraud Investigations Router
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
from dashboard.services.dashboard_service import DashboardService
from storage.database import SessionLocal
from storage.models import EventRecord, PredictionRecord

router = APIRouter(prefix="/api/v1/investigations", tags=["Investigations"])

# In-memory storage for analyst case statuses (Approved, Confirmed Fraud, Under Review)
ANALYST_CASE_STORE: Dict[str, Dict[str, Any]] = {}


@router.get("/cases")
def list_investigation_cases(
    status: Optional[str] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """Retrieves high-priority alert cases for forensic fraud analyst review."""
    dash_service = DashboardService()
    df = dash_service.get_recent_transactions(limit=150)

    if df.empty:
        return {"status": "success", "cases": []}

    # Filter transactions that require investigation (REVIEW, BLOCK, or HIGH_RISK)
    flagged = df[df["action_decision"].isin(["REVIEW", "BLOCK"])].copy()

    cases = []
    for _, row in flagged.head(limit).iterrows():
        eid = row["event_id"]
        analyst_override = ANALYST_CASE_STORE.get(eid, {})

        case_status = analyst_override.get("status", "OPEN_REVIEW" if row["action_decision"] == "REVIEW" else "OPEN_CRITICAL")
        if status and case_status != status:
            continue

        evidence = []
        try:
            evidence = json.loads(row.get("evidence_json", "[]"))
        except Exception:
            evidence = []

        ts = row["timestamp"].isoformat() if isinstance(row["timestamp"], datetime) else str(row["timestamp"])

        cases.append({
            "case_id": f"CASE-{eid[:8].upper()}",
            "event_id": eid,
            "transaction_id": row["transaction_id"],
            "timestamp": ts,
            "sender_id": row["sender_id"],
            "receiver_id": row["receiver_id"],
            "amount": row["amount"],
            "fraud_probability": row["fraud_probability"],
            "anomaly_score": row["anomaly_score"],
            "system_decision": row["decision"],
            "system_action": row["action_decision"],
            "analyst_status": case_status,
            "assigned_analyst": analyst_override.get("analyst", "Unassigned"),
            "notes": analyst_override.get("notes", ""),
            "evidence_count": len(evidence),
            "evidence_summary": [e.get("detail", "") for e in evidence[:2]],
        })

    return {
        "status": "success",
        "total": len(cases),
        "cases": cases,
    }


@router.get("/cases/{event_id}")
def get_case_detail(event_id: str) -> Dict[str, Any]:
    """Retrieves full case dossier with correlated timeline and deep evidence breakdown."""
    dash_service = DashboardService()
    detail = dash_service.get_transaction_detail(event_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Case with event_id '{event_id}' not found.")

    sender_id = detail.get("sender_id")
    device_id = detail.get("device_id")

    # Find related transactions from same sender or device to build timeline
    session = SessionLocal()
    timeline = []
    try:
        related_events = (
            session.query(EventRecord, PredictionRecord)
            .outerjoin(PredictionRecord, EventRecord.event_id == PredictionRecord.event_id)
            .filter((EventRecord.device_id == device_id) | (EventRecord.session_id == detail.get("session_id")))
            .order_by(EventRecord.timestamp.desc())
            .limit(10)
            .all()
        )

        for evt, pred in related_events:
            ts = evt.timestamp.isoformat() if isinstance(evt.timestamp, datetime) else str(evt.timestamp)
            timeline.append({
                "event_id": evt.event_id,
                "timestamp": ts,
                "amount": evt.amount,
                "decision": pred.decision if pred else "UNKNOWN",
                "fraud_probability": pred.fraud_probability if pred else 0.0,
            })
    finally:
        session.close()

    analyst_override = ANALYST_CASE_STORE.get(event_id, {})
    if isinstance(detail.get("timestamp"), datetime):
        detail["timestamp"] = detail["timestamp"].isoformat()

    return {
        "status": "success",
        "case": {
            "case_id": f"CASE-{event_id[:8].upper()}",
            "transaction": detail,
            "timeline": timeline,
            "analyst_state": analyst_override,
        },
    }


@router.post("/cases/{event_id}/action")
def update_case_action(
    event_id: str,
    action: str = Body(..., embed=True),  # APPROVE, CONFIRM_FRAUD, ESCALATE, ADD_WATCHLIST
    notes: Optional[str] = Body("", embed=True),
    analyst: Optional[str] = Body("Operator_1", embed=True),
) -> Dict[str, Any]:
    """Applies a formal analyst action / remediation decision to an active case."""
    ANALYST_CASE_STORE[event_id] = {
        "status": action,
        "notes": notes,
        "analyst": analyst,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    return {
        "status": "success",
        "message": f"Action '{action}' recorded for case {event_id[:8]}",
        "data": ANALYST_CASE_STORE[event_id],
    }

