"""
DRIFTGUARD SQLite Database Models
SQLAlchemy ORM tables providing persistent event, prediction, security, and drift storage.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    Text,
    Index,
    UniqueConstraint,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utc_now() -> datetime:
    """Return timezone-aware current UTC time."""
    return datetime.now(timezone.utc)


class EventRecord(Base):
    """Stores validated transaction events."""
    __tablename__ = "events"

    event_id = Column(String(64), primary_key=True)
    transaction_id = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    device_id = Column(String(64), nullable=False, index=True)
    session_id = Column(String(64), nullable=False, index=True)
    key_id = Column(String(64), nullable=False, index=True)
    nonce = Column(String(64), nullable=False)
    amount = Column(Float, nullable=False)
    signature = Column(String(256), nullable=False)
    payload_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    prediction = relationship("PredictionRecord", back_populates="event", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_events_key_nonce", "key_id", "nonce"),
    )


class PredictionRecord(Base):
    """Stores model inference, streaming anomaly scores, and decision results."""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), ForeignKey("events.event_id"), unique=True, nullable=False, index=True)
    fraud_probability = Column(Float, nullable=False)
    anomaly_score = Column(Float, nullable=False)
    context_risk = Column(Float, nullable=False)
    decision = Column(String(32), nullable=False, index=True)  # NORMAL, MONITOR, REVIEW, HIGH_RISK, INTEGRITY_REJECTED
    evidence_json = Column(Text, nullable=False)
    model_version = Column(String(64), nullable=False)
    processed_at = Column(DateTime, default=utc_now, nullable=False)

    event = relationship("EventRecord", back_populates="prediction")


class IntegrityLogRecord(Base):
    """Audit log of all event integrity verifications, including rejections."""
    __tablename__ = "integrity_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), nullable=False, index=True)
    key_id = Column(String(64), nullable=False)
    nonce = Column(String(64), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    status = Column(String(32), nullable=False, index=True)  # VALID, REJECTED_BAD_SIG, REJECTED_REPLAY, REJECTED_EXPIRED, etc.
    reason = Column(Text, nullable=False)
    client_ip = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        Index("ix_integrity_key_nonce", "key_id", "nonce"),
    )


class ReplayProtectionRecord(Base):
    """Persistent replay tracking table to ensure atomic rejection of reused nonces and event IDs."""
    __tablename__ = "replay_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_id = Column(String(64), nullable=False)
    nonce = Column(String(64), nullable=False)
    event_id = Column(String(64), nullable=False, unique=True)
    event_timestamp = Column(DateTime, nullable=False)
    recorded_at = Column(DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("key_id", "nonce", name="uq_key_nonce"),
        Index("ix_replay_key_nonce", "key_id", "nonce"),
    )


class DriftEventRecord(Base):
    """Stores detected data or concept drift events."""
    __tablename__ = "drift_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    detector_name = Column(String(64), nullable=False)
    signal_type = Column(String(64), nullable=False, index=True)  # UNLABELLED_ANOMALY, LABELLED_PREDICTION_ERROR, FEATURE_PSI
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)
    observation_count = Column(Integer, nullable=False)
    metric_value = Column(Float, nullable=False)
    details_json = Column(Text, nullable=False)


class ModelVersionRecord(Base):
    """Registry of trained models and baselines."""
    __tablename__ = "model_versions"

    version_id = Column(String(64), primary_key=True)
    model_name = Column(String(64), nullable=False)
    model_type = Column(String(32), nullable=False)  # RANDOM_FOREST, SGD_INCREMENTAL, RIVER_HST, ISOLATION_FOREST
    trained_at = Column(DateTime, default=utc_now, nullable=False)
    metrics_json = Column(Text, nullable=False)
    filepath = Column(String(256), nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)


class ExperimentRunRecord(Base):
    """Tracks synthetic or benchmark simulation runs."""
    __tablename__ = "experiment_runs"

    run_id = Column(String(64), primary_key=True)
    scenario_name = Column(String(64), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    total_events = Column(Integer, default=0, nullable=False)
    rejected_events = Column(Integer, default=0, nullable=False)
    flagged_events = Column(Integer, default=0, nullable=False)
    summary_json = Column(Text, nullable=False)

