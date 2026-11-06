"""
DRIFTGUARD Cryptographic Security and Replay Protection Tests
Verifies Ed25519 signing, signature verification, freshness enforcement, and replay attack prevention.
"""

from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from storage.models import Base
from security.key_manager import KeyManager
from security.signature_verifier import SignatureVerifier
from security.integrity_service import IntegrityService
from ingestion.event_schema import TransactionEvent


@pytest.fixture
def db_session():
    """Provides a fresh, hermetic in-memory SQLite database session."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def key_manager(tmp_path):
    """Provides an isolated KeyManager using a temporary directory."""
    return KeyManager(keys_dir=tmp_path)


def test_key_generation_and_signing(key_manager):
    priv, pub = key_manager.generate_key_pair("test-key")
    assert priv is not None
    assert pub is not None
    assert key_manager.get_public_key("test-key") is not None


def test_valid_event_signature_accepted(db_session, key_manager):
    priv, pub = key_manager.generate_key_pair("key-alpha")
    now = datetime.now(timezone.utc)

    temp_event = TransactionEvent(
        event_id="evt_valid_1",
        transaction_id="tx_valid_1",
        timestamp=now,
        device_id="dev_100",
        session_id="sess_100",
        key_id="key-alpha",
        nonce="nonce_unique_12345",
        amount=75.0,
        signature="placeholder_sig_32_characters_minimum",
    )
    sig = SignatureVerifier.sign_event(temp_event, priv)
    valid_event = TransactionEvent(**{**temp_event.model_dump(), "signature": sig})

    service = IntegrityService(session=db_session, key_manager=key_manager)
    result = service.verify_event(valid_event)

    assert result.is_valid is True
    assert result.status == "VALID"


def test_modified_payload_rejected(db_session, key_manager):
    priv, _ = key_manager.generate_key_pair("key-alpha")
    now = datetime.now(timezone.utc)

    temp_event = TransactionEvent(
        event_id="evt_tamper_1",
        transaction_id="tx_tamper_1",
        timestamp=now,
        device_id="dev_100",
        session_id="sess_100",
        key_id="key-alpha",
        nonce="nonce_tamper_12345",
        amount=50.0,
        signature="placeholder_sig_32_characters_minimum",
    )
    sig = SignatureVerifier.sign_event(temp_event, priv)

    # Adversary alters amount from 50.0 to 5000.0 without changing signature
    tampered_event = TransactionEvent(
        **{**temp_event.model_dump(), "amount": 5000.0, "signature": sig}
    )

    service = IntegrityService(session=db_session, key_manager=key_manager)
    result = service.verify_event(tampered_event)

    assert result.is_valid is False
    assert result.status == "REJECTED_BAD_SIG"


def test_unknown_key_rejected(db_session, key_manager):
    now = datetime.now(timezone.utc)
    event = TransactionEvent(
        event_id="evt_unknown_key",
        transaction_id="tx_unknown_key",
        timestamp=now,
        device_id="dev_100",
        session_id="sess_100",
        key_id="non-existent-key-id",
        nonce="nonce_unknown_12345",
        amount=50.0,
        signature="deadbeef" * 8,
    )
    service = IntegrityService(session=db_session, key_manager=key_manager)
    result = service.verify_event(event)

    assert result.is_valid is False
    assert result.status == "REJECTED_UNKNOWN_KEY"


def test_expired_event_rejected(db_session, key_manager):
    priv, _ = key_manager.generate_key_pair("key-alpha")
    # Event timestamp is 1 hour in the past
    stale_time = datetime.now(timezone.utc) - timedelta(seconds=3600)

    temp_event = TransactionEvent(
        event_id="evt_stale_1",
        transaction_id="tx_stale_1",
        timestamp=stale_time,
        device_id="dev_100",
        session_id="sess_100",
        key_id="key-alpha",
        nonce="nonce_stale_12345",
        amount=75.0,
        signature="placeholder_sig_32_characters_minimum",
    )
    sig = SignatureVerifier.sign_event(temp_event, priv)
    event = TransactionEvent(**{**temp_event.model_dump(), "signature": sig})

    service = IntegrityService(session=db_session, key_manager=key_manager, enforce_freshness=True)
    result = service.verify_event(event)

    assert result.is_valid is False
    assert result.status == "REJECTED_EXPIRED"


def test_replayed_nonce_rejected(db_session, key_manager):
    priv, _ = key_manager.generate_key_pair("key-alpha")
    now = datetime.now(timezone.utc)

    temp_event_1 = TransactionEvent(
        event_id="evt_replay_first",
        transaction_id="tx_first",
        timestamp=now,
        device_id="dev_100",
        session_id="sess_100",
        key_id="key-alpha",
        nonce="shared_nonce_99999",
        amount=100.0,
        signature="placeholder_sig_32_characters_minimum",
    )
    sig1 = SignatureVerifier.sign_event(temp_event_1, priv)
    event1 = TransactionEvent(**{**temp_event_1.model_dump(), "signature": sig1})

    service = IntegrityService(session=db_session, key_manager=key_manager)
    res1 = service.verify_event(event1)
    assert res1.is_valid is True

    # Second event tries to reuse the exact same nonce with a different event_id
    temp_event_2 = TransactionEvent(
        event_id="evt_replay_second",
        transaction_id="tx_second",
        timestamp=now,
        device_id="dev_100",
        session_id="sess_100",
        key_id="key-alpha",
        nonce="shared_nonce_99999",
        amount=200.0,
        signature="placeholder_sig_32_characters_minimum",
    )
    sig2 = SignatureVerifier.sign_event(temp_event_2, priv)
    event2 = TransactionEvent(**{**temp_event_2.model_dump(), "signature": sig2})

    res2 = service.verify_event(event2)
    assert res2.is_valid is False
    assert res2.status == "REJECTED_REPLAY_NONCE"


def test_duplicate_event_id_rejected(db_session, key_manager):
    priv, _ = key_manager.generate_key_pair("key-alpha")
    now = datetime.now(timezone.utc)

    temp_event = TransactionEvent(
        event_id="evt_duplicate_id",
        transaction_id="tx_orig",
        timestamp=now,
        device_id="dev_100",
        session_id="sess_100",
        key_id="key-alpha",
        nonce="nonce_unique_111",
        amount=50.0,
        signature="placeholder_sig_32_characters_minimum",
    )
    sig = SignatureVerifier.sign_event(temp_event, priv)
    event = TransactionEvent(**{**temp_event.model_dump(), "signature": sig})

    service = IntegrityService(session=db_session, key_manager=key_manager)
    res1 = service.verify_event(event)
    assert res1.is_valid is True

    # Replaying the exact same event
    res2 = service.verify_event(event)
    assert res2.is_valid is False
    assert "REPLAY" in res2.status
