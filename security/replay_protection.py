"""
DRIFTGUARD Replay Protection Service
Enforces strict event timestamp freshness and atomic database-backed nonce/event_id deduplication.
"""

from datetime import datetime, timezone
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from config import settings
from ingestion.event_schema import TransactionEvent
from storage.repositories import ReplayProtectionRepository


class ReplayProtector:
    """
    Prevents replay attacks via:
    1. Timestamp freshness window (rejects stale or far-future events).
    2. Atomic SQLite persistence of nonces and event IDs.
    """

    def __init__(
        self,
        session: Session,
        max_age_seconds: int = settings.MAX_EVENT_AGE_SECONDS,
        max_clock_skew_seconds: int = settings.MAX_CLOCK_SKEW_SECONDS,
    ):
        self.session = session
        self.repo = ReplayProtectionRepository(session)
        self.max_age_seconds = max_age_seconds
        self.max_clock_skew_seconds = max_clock_skew_seconds

    def check_freshness(
        self,
        event: TransactionEvent,
        reference_time: Optional[datetime] = None,
    ) -> Tuple[bool, str]:
        """
        Validates that the event was generated within the allowable time window.
        """
        now = reference_time or datetime.now(timezone.utc)
        event_time = event.timestamp
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone.utc)

        age = (now - event_time).total_seconds()

        if age > self.max_age_seconds:
            return False, f"EVENT_EXPIRED: age={age:.1f}s exceeds limit {self.max_age_seconds}s"

        if age < -self.max_clock_skew_seconds:
            return False, f"FUTURE_TIMESTAMP: event is {-age:.1f}s in the future beyond allowable skew"

        return True, "FRESHNESS_VERIFIED"

    def check_and_record_replay(self, event: TransactionEvent) -> Tuple[bool, str]:
        """
        Atomically records (key_id, nonce) and event_id into SQLite replay table.
        Rejects previously seen nonces or event IDs.
        """
        success, code = self.repo.check_and_record(
            key_id=event.key_id,
            nonce=event.nonce,
            event_id=event.event_id,
            event_timestamp=event.timestamp,
        )
        if not success:
            if code == "REPLAY_EVENT_ID":
                return False, f"DUPLICATE_EVENT_ID: {event.event_id} already processed"
            return False, f"REPLAY_NONCE_REUSED: nonce {event.nonce} already recorded for key {event.key_id}"

        return True, "REPLAY_PROTECTION_PASSED"

