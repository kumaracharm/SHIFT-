"""
DRIFTGUARD Stream Processor
Controls streaming transaction playback, rate-limiting, and dispatch to processing services.
"""

import time
from typing import Generator, Callable, Optional, Dict, Any, List
from ingestion.event_schema import TransactionEvent


class StreamProcessor:
    """
    Consumes events from an input stream (generator or list) and coordinates
    real-time event dispatch with optional throttling.
    """

    def __init__(self, dispatch_fn: Callable[[TransactionEvent], Any]):
        self.dispatch_fn = dispatch_fn
        self.total_processed = 0
        self.total_rejected = 0
        self.total_flagged = 0

    def process_stream(
        self,
        event_stream: Generator[TransactionEvent, None, None],
        event_rate_per_sec: Optional[float] = None,
        max_events: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Executes streaming ingestion over an event generator.
        Optional rate throttling via sleep.
        """
        delay = (1.0 / event_rate_per_sec) if (event_rate_per_sec and event_rate_per_sec > 0) else 0.0
        results: List[Any] = []

        for idx, event in enumerate(event_stream):
            if max_events and idx >= max_events:
                break

            result = self.dispatch_fn(event)
            results.append(result)
            self.total_processed += 1

            if hasattr(result, "decision"):
                if result.decision == "INTEGRITY_REJECTED":
                    self.total_rejected += 1
                elif result.decision in ("HIGH_RISK", "REVIEW"):
                    self.total_flagged += 1

            if delay > 0:
                time.sleep(delay)

        return {
            "total_processed": self.total_processed,
            "total_rejected": self.total_rejected,
            "total_flagged": self.total_flagged,
            "results": results,
        }

