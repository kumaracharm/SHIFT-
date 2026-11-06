"""
DRIFTGUARD End-to-End Pipeline Integration Tests
Verifies the complete lifecycle: event ingestion, cryptographic verification,
feature engineering, supervised & streaming ML inference, drift monitoring,
evidence generation, decision rating, and SQLite persistence.
"""

from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from storage.models import Base
from security.key_manager import KeyManager
from models.fraud_classifier import SupervisedFraudClassifier
from models.prediction_service import PredictionService
from engine.event_service import EventProcessingService
from ingestion.event_generator import StreamEventGenerator
from simulation.scenarios import ScenarioType
from storage.repositories import EventRepository, PredictionRepository, IntegrityLogRepository


@pytest.fixture
def test_env(tmp_path):
    """Sets up an isolated database, key manager, and fitted classifier."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    km = KeyManager(keys_dir=tmp_path / "keys")
    km.generate_key_pair("test-key")

    # Fit a quick baseline classifier
    clf = SupervisedFraudClassifier(n_estimators=10, random_state=42)
    dummy_X = np.ones((50, 8), dtype=np.float32)
    dummy_y = np.array([0] * 45 + [1] * 5, dtype=int)
    clf.fit(dummy_X, dummy_y)

    pred_service = PredictionService(fraud_classifier=clf)
    event_service = EventProcessingService(
        session=session,
        key_manager=km,
        prediction_service=pred_service,
        enforce_freshness=False,  # Allow simulated timestamps
    )

    generator = StreamEventGenerator(key_manager=km, key_id="test-key", seed=42)

    yield {
        "session": session,
        "event_service": event_service,
        "generator": generator,
        "km": km,
    }

    session.close()


import numpy as np


def test_full_pipeline_valid_event_processing(test_env):
    service: EventProcessingService = test_env["event_service"]
    gen: StreamEventGenerator = test_env["generator"]
    session = test_env["session"]

    event = gen.generate_single_event(scenario=ScenarioType.NORMAL)
    result = service.process_event(event)

    assert result.event_id == event.event_id
    assert result.integrity_status == "VALID"
    assert result.decision in ("NORMAL", "MONITOR", "REVIEW", "HIGH_RISK")
    assert 0.0 <= result.fraud_probability <= 1.0
    assert 0.0 <= result.anomaly_score <= 1.0
    assert len(result.evidence) > 0
    assert result.processing_timestamp is not None

    # Verify SQLite persistence
    event_repo = EventRepository(session)
    pred_repo = PredictionRepository(session)

    persisted_event = event_repo.get_event(event.event_id)
    assert persisted_event is not None
    assert persisted_event.amount == event.amount

    persisted_pred = pred_repo.get_prediction(event.event_id)
    assert persisted_pred is not None
    assert persisted_pred.decision == result.decision


def test_full_pipeline_tampered_payload_rejected(test_env):
    service: EventProcessingService = test_env["event_service"]
    gen: StreamEventGenerator = test_env["generator"]
    session = test_env["session"]

    tampered_event = gen.generate_single_event(scenario=ScenarioType.NORMAL, tamper_signature=True)
    result = service.process_event(tampered_event)

    assert result.integrity_status == "REJECTED_BAD_SIG"
    assert result.decision == "INTEGRITY_REJECTED"
    assert any("CRYPTOGRAPHIC_INTEGRITY" in e.get("factor", "") for e in result.evidence)

    # Verify rejection was logged in integrity_logs
    log_repo = IntegrityLogRepository(session)
    logs = log_repo.list_logs(status="REJECTED_BAD_SIG")
    assert len(logs) >= 1
    assert logs[0].event_id == tampered_event.event_id


def test_full_pipeline_replay_attack_rejected(test_env):
    service: EventProcessingService = test_env["event_service"]
    gen: StreamEventGenerator = test_env["generator"]

    event = gen.generate_single_event(scenario=ScenarioType.NORMAL)

    # First presentation: accepted
    r1 = service.process_event(event)
    assert r1.integrity_status == "VALID"

    # Second presentation (Replay attack): rejected
    r2 = service.process_event(event)
    assert r2.decision == "INTEGRITY_REJECTED"
    assert "REPLAY" in r2.integrity_status

