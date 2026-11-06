"""
DRIFTGUARD Feature Engineering Pipeline Tests
Verifies temporal feature extraction, velocity tracking, contextual consistency, and vector formatting.
"""

from datetime import datetime, timezone, timedelta
import numpy as np
import pytest
from ingestion.event_schema import TransactionEvent
from features.feature_pipeline import FeaturePipeline, ORDERED_FEATURE_NAMES


def make_event(
    event_id: str = "evt_test",
    amount: float = 100.0,
    timestamp: datetime = None,
    device_id: str = "dev_phone_1",
    session_id: str = "sess_1",
    asn: int = 15169,
    is_vpn: bool = False,
):
    ts = timestamp or datetime.now(timezone.utc)
    return TransactionEvent(
        event_id=event_id,
        transaction_id=f"tx_{event_id}",
        timestamp=ts,
        device_id=device_id,
        session_id=session_id,
        key_id="test-key",
        nonce=f"nonce_{event_id}_1234",
        amount=amount,
        signature="a" * 64,
        ip_context={"is_vpn": is_vpn},
        asn=asn,
    )


def test_feature_extraction_order_and_shape():
    pipeline = FeaturePipeline()
    event = make_event(amount=50.0)
    feat_dict, feat_vec = pipeline.extract_features(event)

    assert len(feat_vec) == len(ORDERED_FEATURE_NAMES)
    assert feat_dict["amount"] == 50.0
    assert abs(feat_dict["log_amount"] - np.log1p(50.0)) < 1e-4
    assert feat_dict["device_consistency"] == 1.0


def test_velocity_and_time_since_prev():
    pipeline = FeaturePipeline()
    t0 = datetime(2026, 11, 6, 10, 0, 0, tzinfo=timezone.utc)
    e1 = make_event(event_id="e1", timestamp=t0, device_id="dev_shared")
    f1, _ = pipeline.extract_features(e1)
    assert f1["time_since_prev"] == 3600.0  # Initial default

    # Second event 10 seconds later from same device
    t1 = t0 + timedelta(seconds=10)
    e2 = make_event(event_id="e2", timestamp=t1, device_id="dev_shared")
    f2, _ = pipeline.extract_features(e2)
    assert f2["time_since_prev"] == 10.0
    assert f2["transaction_velocity"] >= 2.0


def test_amount_zscore_deviation():
    pipeline = FeaturePipeline()
    t0 = datetime(2026, 11, 6, 10, 0, 0, tzinfo=timezone.utc)

    # Establish baseline of 100.0 amounts
    for i in range(5):
        evt = make_event(event_id=f"base_{i}", amount=100.0, timestamp=t0 + timedelta(seconds=i*10), device_id="dev_std")
        pipeline.extract_features(evt)

    # Now an extreme spike amount
    spike_evt = make_event(event_id="spike", amount=2500.0, timestamp=t0 + timedelta(seconds=60), device_id="dev_std")
    f_spike, _ = pipeline.extract_features(spike_evt)

    # Std deviation of baseline is 0, so fallback handled safely
    assert f_spike["amount_deviation"] > 2000.0


def test_context_device_mismatch():
    pipeline = FeaturePipeline()
    t0 = datetime.now(timezone.utc)

    # Session begins on dev_alpha
    e1 = make_event(event_id="e1", session_id="sess_hijack", device_id="dev_alpha", timestamp=t0)
    f1, _ = pipeline.extract_features(e1)
    assert f1["device_consistency"] == 1.0

    # Same session suddenly switches to dev_beta
    e2 = make_event(event_id="e2", session_id="sess_hijack", device_id="dev_beta", timestamp=t0 + timedelta(seconds=5))
    f2, _ = pipeline.extract_features(e2)
    assert f2["device_consistency"] == 0.0  # Inconsistent device detected

