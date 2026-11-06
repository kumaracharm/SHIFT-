"""
DRIFTGUARD 2.0 Overview & Command Centre Router
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
import pandas as pd
from sqlalchemy import func
from storage.database import SessionLocal
from storage.models import EventRecord, PredictionRecord, IntegrityLogRecord, DriftEventRecord
from dashboard.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/v1/overview", tags=["Overview"])


@router.get("/summary")
def get_overview_summary() -> Dict[str, Any]:
    """Provides high-level system KPIs, decision distribution, and active model status."""
    dash_service = DashboardService()
    kpis = dash_service.get_kpis()
    return {
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": kpis,
    }


@router.get("/trends")
def get_overview_trends() -> Dict[str, Any]:
    """Provides chronological trend data for transactions, fraud rate, and anomaly rate."""
    session = SessionLocal()
    try:
        # Retrieve recent 200 predictions with events
        records = (
            session.query(
                EventRecord.timestamp,
                EventRecord.amount,
                PredictionRecord.fraud_probability,
                PredictionRecord.anomaly_score,
                PredictionRecord.decision,
            )
            .join(PredictionRecord, EventRecord.event_id == PredictionRecord.event_id)
            .order_by(EventRecord.timestamp.asc())
            .limit(200)
            .all()
        )

        timestamps = []
        amounts = []
        fraud_probs = []
        anomaly_scores = []
        decisions = []

        for r in records:
            ts_str = r.timestamp.strftime("%H:%M:%S") if r.timestamp else ""
            timestamps.append(ts_str)
            amounts.append(float(r.amount))
            fraud_probs.append(round(float(r.fraud_probability), 4))
            anomaly_scores.append(round(float(r.anomaly_score), 4))
            decisions.append(r.decision)

        return {
            "status": "success",
            "data": {
                "timestamps": timestamps,
                "amounts": amounts,
                "fraud_probabilities": fraud_probs,
                "anomaly_scores": anomaly_scores,
                "decisions": decisions,
            },
        }
    finally:
        session.close()


@router.get("/alerts")
def get_recent_alerts(limit: int = 10) -> Dict[str, Any]:
    """Retrieves recent high-severity operational alerts."""
    session = SessionLocal()
    try:
        # 1. Integrity rejections
        rej_logs = (
            session.query(IntegrityLogRecord)
            .filter(IntegrityLogRecord.status != "VALID")
            .order_by(IntegrityLogRecord.created_at.desc())
            .limit(limit)
            .all()
        )

        # 2. High risk predictions
        high_risk_preds = (
            session.query(PredictionRecord, EventRecord)
            .join(EventRecord, PredictionRecord.event_id == EventRecord.event_id)
            .filter(PredictionRecord.decision.in_(["HIGH_RISK", "INTEGRITY_REJECTED"]))
            .order_by(PredictionRecord.processed_at.desc())
            .limit(limit)
            .all()
        )

        alerts = []
        for r in rej_logs:
            alerts.append({
                "id": f"int-{r.id}",
                "timestamp": r.created_at.isoformat(),
                "severity": "CRITICAL",
                "category": "SECURITY_INTEGRITY",
                "title": f"Security Rejection: {r.status}",
                "detail": r.reason,
                "event_id": r.event_id,
            })

        for p, e in high_risk_preds:
            alerts.append({
                "id": f"pred-{p.id}",
                "timestamp": p.processed_at.isoformat(),
                "severity": "HIGH",
                "category": "FRAUD_DETECTION",
                "title": f"High Risk Transaction Flagged",
                "detail": f"Amount ₹{e.amount:,.2f} | Fraud Prob: {p.fraud_probability:.1%}",
                "event_id": p.event_id,
            })

        alerts.sort(key=lambda x: x["timestamp"], reverse=True)

        return {
            "status": "success",
            "data": alerts[:limit],
        }
    finally:
        session.close()

