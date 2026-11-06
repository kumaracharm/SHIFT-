"""
DRIFTGUARD Drift Detection Tests
Verifies ADWIN unlabelled anomaly monitor, ADWIN labelled error monitor,
Population Stability Index (PSI) feature monitor, and drift persistence.
"""

from datetime import datetime, timezone
import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from storage.models import Base
from drift.adwin_monitor import ADWINChannelMonitor
from drift.feature_monitor import FeatureDistributionMonitor
from drift.drift_manager import DriftManager


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_adwin_unlabelled_anomaly_drift():
    monitor = ADWINChannelMonitor(signal_type="unlabelled_anomaly", delta=0.002)
    rng = np.random.default_rng(42)

    drift_points = []
    # Feed 400 low anomaly scores
    for i in range(400):
        val = float(rng.normal(0.1, 0.02))
        drift, _ = monitor.update(val)
        if drift:
            drift_points.append(i)

    # Abrupt shift to high anomaly scores
    for i in range(400, 800):
        val = float(rng.normal(0.9, 0.02))
        drift, _ = monitor.update(val)
        if drift:
            drift_points.append(i)

    # ADWIN must detect the shift after index 400
    assert len(drift_points) > 0
    assert any(p >= 400 for p in drift_points)
    assert monitor.drift_count >= 1


def test_adwin_labelled_concept_drift(db_session):
    manager = DriftManager(session=db_session)

    # Initial period: low errors (|0 - 0.05| = 0.05)
    for _ in range(300):
        manager.observe_ground_truth(y_true=0, predicted_prob=0.05)

    # Concept shift period: model persistently misclassifies (|1 - 0.05| = 0.95 error)
    detected = False
    for _ in range(300):
        is_drift, status, _ = manager.observe_ground_truth(y_true=1, predicted_prob=0.05)
        if is_drift:
            detected = True
            assert status == "CONCEPT_DRIFT_DETECTED"
            break

    assert detected is True

    # Verify drift was logged in SQLite database
    drifts = manager.repo.list_drift_events()
    assert len(drifts) >= 1
    assert drifts[0].signal_type == "labelled_error"


def test_feature_psi_stability_and_drift():
    monitor = FeatureDistributionMonitor(
        feature_names=["amount"],
        reference_window_size=200,
        stream_window_size=100,
        moderate_threshold=0.10,
        high_threshold=0.20,
    )
    rng = np.random.default_rng(42)

    # Populate reference with normal amounts (mean 50)
    for _ in range(200):
        monitor.update({"amount": float(rng.normal(50.0, 5.0))})

    # 1. Test Stable: stream samples also from mean 50
    for _ in range(100):
        monitor.update({"amount": float(rng.normal(50.0, 5.0))})

    psi_stable, status_stable = monitor.calculate_psi_for_feature("amount")
    assert status_stable == "STABLE"
    assert psi_stable < 0.10

    # 2. Test Significant Drift: stream samples shift drastically to mean 500
    for _ in range(100):
        monitor.update({"amount": float(rng.normal(500.0, 50.0))})

    psi_drift, status_drift = monitor.calculate_psi_for_feature("amount")
    assert status_drift == "SIGNIFICANT_DRIFT"
    assert psi_drift > 0.20

