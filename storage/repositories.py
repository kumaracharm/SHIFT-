"""
DRIFTGUARD SQLite Repository Layer
Thread-safe, transaction-managed operations for events, security logs, predictions, drift, and model versions.
"""

import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from storage.models import (
    EventRecord,
    PredictionRecord,
    IntegrityLogRecord,
    ReplayProtectionRecord,
    DriftEventRecord,
    ModelVersionRecord,
    ExperimentRunRecord,
    utc_now,
)


class EventRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_event(self, event_data: Dict[str, Any], commit: bool = True) -> EventRecord:
        record = EventRecord(
            event_id=event_data["event_id"],
            transaction_id=event_data["transaction_id"],
            timestamp=event_data["timestamp"],
            device_id=event_data["device_id"],
            session_id=event_data["session_id"],
            key_id=event_data["key_id"],
            nonce=event_data["nonce"],
            amount=float(event_data["amount"]),
            signature=event_data["signature"],
            payload_json=json.dumps(event_data.get("payload_json", event_data), default=str),
            created_at=utc_now(),
        )
        self.session.add(record)
        if commit:
            self.session.commit()
        return record

    def get_event(self, event_id: str) -> Optional[EventRecord]:
        return self.session.query(EventRecord).filter(EventRecord.event_id == event_id).first()

    def list_events(self, limit: int = 100, offset: int = 0) -> List[EventRecord]:
        return (
            self.session.query(EventRecord)
            .order_by(EventRecord.timestamp.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )


class PredictionRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_prediction(self, prediction_data: Dict[str, Any], commit: bool = True) -> PredictionRecord:
        evidence = prediction_data.get("evidence", [])
        if isinstance(evidence, (list, dict)):
            evidence_str = json.dumps(evidence)
        else:
            evidence_str = str(evidence)

        record = PredictionRecord(
            event_id=prediction_data["event_id"],
            fraud_probability=float(prediction_data["fraud_probability"]),
            anomaly_score=float(prediction_data["anomaly_score"]),
            context_risk=float(prediction_data["context_risk"]),
            decision=prediction_data["decision"],
            evidence_json=evidence_str,
            model_version=prediction_data["model_version"],
            processed_at=prediction_data.get("processing_timestamp", utc_now()),
        )
        self.session.add(record)
        if commit:
            self.session.commit()
        return record

    def get_prediction(self, event_id: str) -> Optional[PredictionRecord]:
        return self.session.query(PredictionRecord).filter(PredictionRecord.event_id == event_id).first()

    def list_predictions(self, limit: int = 100, decision: Optional[str] = None) -> List[PredictionRecord]:
        query = self.session.query(PredictionRecord)
        if decision:
            query = query.filter(PredictionRecord.decision == decision)
        return query.order_by(PredictionRecord.processed_at.desc()).limit(limit).all()


class IntegrityLogRepository:
    def __init__(self, session: Session):
        self.session = session

    def log_integrity(
        self,
        event_id: str,
        key_id: str,
        nonce: str,
        timestamp: datetime,
        status: str,
        reason: str,
        client_ip: Optional[str] = None,
        commit: bool = True,
    ) -> IntegrityLogRecord:
        record = IntegrityLogRecord(
            event_id=event_id,
            key_id=key_id,
            nonce=nonce,
            timestamp=timestamp,
            status=status,
            reason=reason,
            client_ip=client_ip,
            created_at=utc_now(),
        )
        self.session.add(record)
        if commit:
            self.session.commit()
        return record

    def list_logs(self, limit: int = 100, status: Optional[str] = None) -> List[IntegrityLogRecord]:
        query = self.session.query(IntegrityLogRecord)
        if status:
            query = query.filter(IntegrityLogRecord.status == status)
        return query.order_by(IntegrityLogRecord.created_at.desc()).limit(limit).all()


class ReplayProtectionRepository:
    def __init__(self, session: Session):
        self.session = session

    def check_and_record(
        self,
        key_id: str,
        nonce: str,
        event_id: str,
        event_timestamp: datetime,
    ) -> Tuple[bool, str]:
        """
        Atomically checks if (key_id, nonce) or event_id was already observed.
        If not, persists the record.
        Returns:
            (True, "OK") if accepted.
            (False, "REPLAY_EVENT_ID") if event_id already exists.
            (False, "REPLAY_NONCE") if nonce already used for this key_id.
        """
        # First fast check
        existing_event = self.session.query(ReplayProtectionRecord).filter_by(event_id=event_id).first()
        if existing_event:
            return False, "REPLAY_EVENT_ID"

        existing_nonce = self.session.query(ReplayProtectionRecord).filter_by(key_id=key_id, nonce=nonce).first()
        if existing_nonce:
            return False, "REPLAY_NONCE"

        # Safe insert with savepoint / integrity handling
        record = ReplayProtectionRecord(
            key_id=key_id,
            nonce=nonce,
            event_id=event_id,
            event_timestamp=event_timestamp,
            recorded_at=utc_now(),
        )
        try:
            self.session.add(record)
            self.session.commit()
            return True, "OK"
        except IntegrityError as exc:
            self.session.rollback()
            err_msg = str(exc).lower()
            if "event_id" in err_msg:
                return False, "REPLAY_EVENT_ID"
            return False, "REPLAY_NONCE"


class DriftRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_drift_event(
        self,
        detector_name: str,
        signal_type: str,
        timestamp: datetime,
        observation_count: int,
        metric_value: float,
        details: Dict[str, Any],
        commit: bool = True,
    ) -> DriftEventRecord:
        record = DriftEventRecord(
            detector_name=detector_name,
            signal_type=signal_type,
            timestamp=timestamp,
            observation_count=observation_count,
            metric_value=metric_value,
            details_json=json.dumps(details),
        )
        self.session.add(record)
        if commit:
            self.session.commit()
        return record

    def list_drift_events(self, limit: int = 100) -> List[DriftEventRecord]:
        return (
            self.session.query(DriftEventRecord)
            .order_by(DriftEventRecord.timestamp.desc())
            .limit(limit)
            .all()
        )


class ModelVersionRepository:
    def __init__(self, session: Session):
        self.session = session

    def register_version(
        self,
        version_id: str,
        model_name: str,
        model_type: str,
        metrics: Dict[str, Any],
        filepath: Optional[str] = None,
        is_active: bool = True,
        commit: bool = True,
    ) -> ModelVersionRecord:
        if is_active:
            # Set other active models of this type to inactive
            self.session.query(ModelVersionRecord).filter(
                ModelVersionRecord.model_type == model_type,
                ModelVersionRecord.is_active == True,
            ).update({"is_active": False})

        existing = self.session.query(ModelVersionRecord).filter(ModelVersionRecord.version_id == version_id).first()
        if existing:
            existing.model_name = model_name
            existing.model_type = model_type
            existing.trained_at = utc_now()
            existing.metrics_json = json.dumps(metrics)
            existing.filepath = filepath
            existing.is_active = is_active
            record = existing
        else:
            record = ModelVersionRecord(
                version_id=version_id,
                model_name=model_name,
                model_type=model_type,
                trained_at=utc_now(),
                metrics_json=json.dumps(metrics),
                filepath=filepath,
                is_active=is_active,
            )
            self.session.add(record)
        if commit:
            self.session.commit()
        return record

    def get_active_version(self, model_type: str) -> Optional[ModelVersionRecord]:
        return (
            self.session.query(ModelVersionRecord)
            .filter(ModelVersionRecord.model_type == model_type, ModelVersionRecord.is_active == True)
            .order_by(ModelVersionRecord.trained_at.desc())
            .first()
        )

    def list_versions(self) -> List[ModelVersionRecord]:
        return self.session.query(ModelVersionRecord).order_by(ModelVersionRecord.trained_at.desc()).all()


class ExperimentRunRepository:
    def __init__(self, session: Session):
        self.session = session

    def record_run(
        self,
        run_id: str,
        scenario_name: str,
        start_time: datetime,
        end_time: Optional[datetime],
        total_events: int,
        rejected_events: int,
        flagged_events: int,
        summary: Dict[str, Any],
        commit: bool = True,
    ) -> ExperimentRunRecord:
        record = ExperimentRunRecord(
            run_id=run_id,
            scenario_name=scenario_name,
            start_time=start_time,
            end_time=end_time,
            total_events=total_events,
            rejected_events=rejected_events,
            flagged_events=flagged_events,
            summary_json=json.dumps(summary),
        )
        self.session.add(record)
        if commit:
            self.session.commit()
        return record

    def list_runs(self, limit: int = 100) -> List[ExperimentRunRecord]:
        return (
            self.session.query(ExperimentRunRecord)
            .order_by(ExperimentRunRecord.start_time.desc())
            .limit(limit)
            .all()
        )

    def get_run(self, run_id: str) -> Optional[ExperimentRunRecord]:
        return (
            self.session.query(ExperimentRunRecord)
            .filter(ExperimentRunRecord.run_id == run_id)
            .first()
        )

    def clear_simulation_data(self) -> None:
        """Safely resets simulation tables while preserving trained models and cryptographic keys."""
        self.session.query(PredictionRecord).delete()
        self.session.query(EventRecord).delete()
        self.session.query(IntegrityLogRecord).delete()
        self.session.query(ReplayProtectionRecord).delete()
        self.session.query(DriftEventRecord).delete()
        self.session.query(ExperimentRunRecord).delete()
        self.session.commit()

