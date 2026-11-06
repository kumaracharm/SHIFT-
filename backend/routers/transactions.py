"""
DRIFTGUARD 2.0 Live Transactions Router
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from dashboard.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/v1/transactions", tags=["Transactions"])


@router.get("")
def list_transactions(
    limit: int = 50,
    offset: int = 0,
    decision: Optional[str] = None,
    action: Optional[str] = None,
    search: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieves paginated, filtered, enriched transaction events."""
    dash_service = DashboardService()
    df = dash_service.get_recent_transactions(limit=limit + offset + 100)

    if df.empty:
        return {
            "status": "success",
            "total": 0,
            "data": [],
            "page": offset // limit + 1,
            "limit": limit,
        }

    # Filtering
    if decision and isinstance(decision, str):
        df = df[df["decision"].str.upper() == decision.upper()]
    if action and isinstance(action, str):
        df = df[df["action_decision"].str.upper() == action.upper()]
    if search and isinstance(search, str):
        s = search.lower()
        mask = (
            df["transaction_id"].astype(str).str.lower().str.contains(s)
            | df["sender_id"].astype(str).str.lower().str.contains(s)
            | df["receiver_id"].astype(str).str.lower().str.contains(s)
            | df["location"].astype(str).str.lower().str.contains(s)
            | df["event_id"].astype(str).str.lower().str.contains(s)
        )
        df = df[mask]

    total_matching = len(df)
    sliced = df.iloc[offset : offset + limit]

    records = []
    for _, row in sliced.iterrows():
        rec = row.to_dict()
        if isinstance(rec.get("timestamp"), datetime):
            rec["timestamp"] = rec["timestamp"].isoformat()
        records.append(rec)

    return {
        "status": "success",
        "total": total_matching,
        "data": records,
        "page": offset // limit + 1,
        "limit": limit,
    }


@router.get("/{event_id}")
def get_transaction_detail(event_id: str) -> Dict[str, Any]:
    """Fetches complete cryptographic, prediction, and feature telemetry for a transaction."""
    dash_service = DashboardService()
    detail = dash_service.get_transaction_detail(event_id=event_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Transaction with event_id '{event_id}' not found.")

    if isinstance(detail.get("timestamp"), datetime):
        detail["timestamp"] = detail["timestamp"].isoformat()

    return {
        "status": "success",
        "data": detail,
    }
