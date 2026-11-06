"""
DRIFTGUARD Central Integrity Service
Coordinates cryptographic key lookup, Ed25519 signature verification, freshness enforcement,
atomic SQLite replay protection, and security audit logging.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from ingestion.event_schema import TransactionEvent
from security.key_manager import KeyManager
from security.signature_verifier import SignatureVerifier
from security.replay_protection import ReplayProtector
from storage.repositories import IntegrityLogRepository


@dataclass
class IntegrityResult:
    """Outcome of cryptographic and replay integrity verification."""
    is_valid: bool
    status: str  # VALID, REJECTED_UNKNOWN_KEY, REJECTED_BAD_SIG, REJECTED_EXPIRED, REJECTED_REPLAY_EVENT_ID, REJECTED_REPLAY_NONCE
    reason: str
    key_id: str
    checked_at: datetime


class IntegrityService:
    """
    Main defense boundary. Ensures untrusted or replayed events are discarded
    and logged before any feature calculation or ML model inference occurs.
    """

    def __init__(
        self,
        session: Session,
        key_manager: KeyManager,
        enforce_freshness: bool = True,
    ):
        self.session = session
        self.key_manager = key_manager
        self.verifier = SignatureVerifier()
        self.replay_protector = ReplayProtector(session=session)
        self.log_repo = IntegrityLogRepository(session=session)
        self.enforce_freshness = enforce_freshness

    def verify_event(
        self,
        event: TransactionEvent,
        client_ip: Optional[str] = None,
        reference_time: Optional[datetime] = None,
    ) -> IntegrityResult:
        now = datetime.now(timezone.utc)

        # 1. Look up trusted public key
        public_key = self.key_manager.get_public_key(event.key_id)
        if not public_key:
            status = "REJECTED_UNKNOWN_KEY"
            reason = f"Public key with key_id '{event.key_id}' is not in trusted keystore"
            self.log_repo.log_integrity(
                event_id=event.event_id,
                key_id=event.key_id,
                nonce=event.nonce,
                timestamp=event.timestamp,
                status=status,
                reason=reason,
                client_ip=client_ip,
            )
            return IntegrityResult(is_valid=False, status=status, reason=reason, key_id=event.key_id, checked_at=now)

        # 2. Verify Ed25519 signature over canonical payload
        sig_valid, sig_reason = self.verifier.verify_event(event, public_key)
        if not sig_valid:
            status = "REJECTED_BAD_SIG"
            reason = f"Cryptographic signature check failed: {sig_reason}"
            self.log_repo.log_integrity(
                event_id=event.event_id,
                key_id=event.key_id,
                nonce=event.nonce,
                timestamp=event.timestamp,
                status=status,
                reason=reason,
                client_ip=client_ip,
            )
            return IntegrityResult(is_valid=False, status=status, reason=reason, key_id=event.key_id, checked_at=now)

        # 3. Check Freshness Window (if enabled)
        if self.enforce_freshness:
            fresh, fresh_reason = self.replay_protector.check_freshness(event, reference_time=reference_time)
            if not fresh:
                status = "REJECTED_EXPIRED" if "EXPIRED" in fresh_reason else "REJECTED_FUTURE_TIMESTAMP"
                self.log_repo.log_integrity(
                    event_id=event.event_id,
                    key_id=event.key_id,
                    nonce=event.nonce,
                    timestamp=event.timestamp,
                    status=status,
                    reason=fresh_reason,
                    client_ip=client_ip,
                )
                return IntegrityResult(is_valid=False, status=status, reason=fresh_reason, key_id=event.key_id, checked_at=now)

        # 4. Atomic Nonce & Event ID Replay Protection
        replay_ok, replay_reason = self.replay_protector.check_and_record_replay(event)
        if not replay_ok:
            status = "REJECTED_REPLAY_EVENT_ID" if "DUPLICATE_EVENT_ID" in replay_reason else "REJECTED_REPLAY_NONCE"
            self.log_repo.log_integrity(
                event_id=event.event_id,
                key_id=event.key_id,
                nonce=event.nonce,
                timestamp=event.timestamp,
                status=status,
                reason=replay_reason,
                client_ip=client_ip,
            )
            return IntegrityResult(is_valid=False, status=status, reason=replay_reason, key_id=event.key_id, checked_at=now)

        # 5. Success - All security checks passed
        status = "VALID"
        reason = "Cryptographic signature, timestamp freshness, and replay uniqueness verified."
        self.log_repo.log_integrity(
            event_id=event.event_id,
            key_id=event.key_id,
            nonce=event.nonce,
            timestamp=event.timestamp,
            status=status,
            reason=reason,
            client_ip=client_ip,
        )
        return IntegrityResult(is_valid=True, status=status, reason=reason, key_id=event.key_id, checked_at=now)

