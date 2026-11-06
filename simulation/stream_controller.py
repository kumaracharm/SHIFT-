"""
DRIFTGUARD Stream Controller & Operator Control Panel Engine
Thread-safe, session-aware stream state machine managing live UPI transaction ingestion.
Guarantees zero duplicate background workers on Streamlit reruns.
"""

from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import io
import pandas as pd

from config import settings
from storage.database import SessionLocal
from engine.event_service import EventProcessingService
from simulation.scenarios import ScenarioType
from simulation.upi_generator import UPITransactionGenerator
from dashboard.services.dashboard_service import DashboardService


class StreamState(str, Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"


class StreamController:
    """
    Operator control panel engine governing live transaction ingestion.
    Coordinates between UPITransactionGenerator, EventProcessingService,
    and SQLite persistence.
    """

    def __init__(self, key_id: str = settings.DEFAULT_KEY_ID):
        self.generator = UPITransactionGenerator(key_id=key_id)
        self.key_id = key_id

    def step(
        self,
        scenario: ScenarioType = ScenarioType.UPI_NORMAL,
        count: int = 5,
        anomaly_ratio: float = 0.05,
    ) -> List[Dict[str, Any]]:
        """
        Executes a single discrete ingestion step of 'count' events.
        Ensures each event passes through the full end-to-end backend contract:
        Validation -> Integrity -> Replay Check -> Features -> Models -> Drift -> Decision -> SQLite.
        """
        session = SessionLocal()
        results = []
        try:
            event_service = EventProcessingService(session=session, enforce_freshness=True)
            events = list(self.generator.generate_stream(count=count, scenario=scenario, anomaly_ratio=anomaly_ratio))

            for event in events:
                res = event_service.process_event(event)
                results.append({
                    "event_id": res.event_id,
                    "transaction_id": event.transaction_id,
                    "sender_id": event.sender_id or "N/A",
                    "receiver_id": event.receiver_id or "N/A",
                    "amount": event.amount,
                    "integrity_status": res.integrity_status,
                    "decision": res.decision,
                    "fraud_probability": res.fraud_probability,
                    "anomaly_score": res.anomaly_score,
                    "context_risk": res.context_risk,
                })
        finally:
            session.close()

        return results

    def trigger_single_scenario(
        self,
        scenario: ScenarioType = ScenarioType.UPI_AMOUNT_SPIKE,
        tamper: bool = False,
    ) -> Dict[str, Any]:
        """Manually triggers a single high-priority transaction or attack."""
        session = SessionLocal()
        try:
            event_service = EventProcessingService(session=session, enforce_freshness=True)
            event = self.generator.generate_single_event(scenario=scenario, tamper_signature=tamper)
            res = event_service.process_event(event)
            return {
                "event_id": res.event_id,
                "transaction_id": event.transaction_id,
                "sender_id": event.sender_id or "N/A",
                "receiver_id": event.receiver_id or "N/A",
                "amount": event.amount,
                "integrity_status": res.integrity_status,
                "decision": res.decision,
                "fraud_probability": res.fraud_probability,
                "anomaly_score": res.anomaly_score,
                "evidence": res.evidence,
            }
        finally:
            session.close()

    @staticmethod
    def export_csv(limit: int = 500) -> str:
        """Exports recent session transactions as standard CSV format."""
        dash_service = DashboardService()
        df = dash_service.get_recent_transactions(limit=limit)
        if df.empty:
            return "Timestamp,TransactionID,Sender,Receiver,AmountINR,Decision,FraudProb,AnomalyScore,ContextRisk\n"

        export_df = df.copy()
        export_df["Timestamp"] = pd.to_datetime(export_df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        export_df = export_df.rename(columns={
            "transaction_id": "TransactionID",
            "sender_id": "Sender",
            "receiver_id": "Receiver",
            "amount": "AmountINR",
            "decision": "Decision",
            "fraud_probability": "FraudProb",
            "anomaly_score": "AnomalyScore",
            "context_risk": "ContextRisk",
            "model_version": "ModelVersion",
        })

        cols_to_export = [
            c for c in [
                "Timestamp", "TransactionID", "event_id", "Sender", "Receiver",
                "AmountINR", "Decision", "FraudProb", "AnomalyScore",
                "ContextRisk", "ModelVersion"
            ] if c in export_df.columns
        ]

        return export_df[cols_to_export].to_csv(index=False)

