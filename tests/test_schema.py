"""
DRIFTGUARD Schema Tests
Verifies Pydantic transaction event schema, canonical serialization, and input validation boundaries.
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from ingestion.event_schema import TransactionEvent


def test_valid_transaction_event():
    event = TransactionEvent(
        event_id="evt_12345",
        transaction_id="tx_98765",
        timestamp=datetime.now(timezone.utc),
        device_id="dev_macbook_01",
        session_id="sess_abc123",
        key_id="test-key-1",
        nonce="0123456789abcdef",
        amount=149.99,
        signature="a" * 64,
        transaction_velocity=2.0,
        device_context={"os": "macOS", "browser": "Chrome"},
        ip_context={"ip_address": "192.168.1.1", "is_vpn": False},
        asn=15169,
        dataset_source="synthetic",
    )
    assert event.event_id == "evt_12345"
    assert event.amount == 149.99
    assert event.timestamp.tzinfo == timezone.utc


def test_invalid_negative_amount():
    with pytest.raises(ValidationError):
        TransactionEvent(
            event_id="evt_12345",
            transaction_id="tx_98765",
            timestamp=datetime.now(timezone.utc),
            device_id="dev_macbook_01",
            session_id="sess_abc123",
            key_id="test-key-1",
            nonce="0123456789abcdef",
            amount=-50.0,
            signature="a" * 64,
        )


def test_empty_required_field():
    with pytest.raises(ValidationError):
        TransactionEvent(
            event_id="",  # Empty event_id
            transaction_id="tx_98765",
            timestamp=datetime.now(timezone.utc),
            device_id="dev_macbook_01",
            session_id="sess_abc123",
            key_id="test-key-1",
            nonce="0123456789abcdef",
            amount=10.0,
            signature="a" * 64,
        )


def test_missing_optional_context_handled():
    event = TransactionEvent(
        event_id="evt_minimal",
        transaction_id="tx_minimal",
        timestamp=datetime.now(timezone.utc),
        device_id="dev_01",
        session_id="sess_01",
        key_id="test-key",
        nonce="nonce12345678",
        amount=10.0,
        signature="a" * 64,
    )
    assert event.transaction_velocity is None
    assert event.device_context is None
    assert event.ip_context is None
    assert event.dataset_source == "synthetic"


def test_canonical_bytes_excludes_signature():
    event = TransactionEvent(
        event_id="evt_canon",
        transaction_id="tx_canon",
        timestamp=datetime(2026, 11, 6, 12, 0, 0, tzinfo=timezone.utc),
        device_id="dev_canon",
        session_id="sess_canon",
        key_id="key_canon",
        nonce="nonce_canon_1234",
        amount=99.50,
        signature="signature_to_be_excluded_from_hash",
    )
    canonical_dict = event.to_canonical_dict()
    assert "signature" not in canonical_dict
    assert canonical_dict["amount"] == 99.50

    canonical_bytes = event.get_canonical_bytes()
    assert b"signature_to_be_excluded" not in canonical_bytes
    assert b"evt_canon" in canonical_bytes

