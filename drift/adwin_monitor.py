"""
DRIFTGUARD ADWIN Drift Monitor
Wraps River's ADWIN adaptive sliding window algorithm to monitor statistical signals:
1. Unlabelled signal: streaming anomaly score distribution shifts.
2. Labelled signal: classification error shifts when verified fraud labels arrive.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
from river.drift import ADWIN
from config import settings


class ADWINSignalType:
    UNLABELLED_ANOMALY = "unlabelled_anomaly"
    LABELLED_ERROR = "labelled_error"


class ADWINChannelMonitor:
    """
    Manages an independent ADWIN window for a dedicated telemetry stream.
    Detects significant changes in the mean of the monitored signal without false-positive cascades.
    """

    def __init__(
        self,
        signal_type: str,
        delta: float = settings.ADWIN_DELTA,
        clock: int = settings.ADWIN_CLOCK,
    ):
        self.signal_type = signal_type
        self.delta = delta
        self.clock = clock
        self.detector = ADWIN(delta=delta, clock=clock)
        self.observation_count = 0
        self.drift_count = 0
        self.last_drift_timestamp: Optional[datetime] = None

    def update(
        self,
        value: float,
        timestamp: Optional[datetime] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Updates the ADWIN detector with the next observed value.
        Returns: (is_drift_detected, metrics_dictionary)
        """
        ts = timestamp or datetime.now(timezone.utc)
        self.observation_count += 1
        self.detector.update(float(value))

        drift_detected = bool(self.detector.drift_detected)
        if drift_detected:
            self.drift_count += 1
            self.last_drift_timestamp = ts

        details = {
            "signal_type": self.signal_type,
            "observation_count": self.observation_count,
            "drift_detected": drift_detected,
            "total_drifts": self.drift_count,
            "estimation": float(self.detector.estimation),
            "variance": float(self.detector.variance),
            "width": int(self.detector.width),
            "timestamp": ts.isoformat(),
        }

        return drift_detected, details

    def get_state(self) -> Dict[str, Any]:
        """Returns snapshot of current window telemetry."""
        return {
            "signal_type": self.signal_type,
            "observation_count": self.observation_count,
            "drift_count": self.drift_count,
            "estimation": float(self.detector.estimation),
            "variance": float(self.detector.variance),
            "width": int(self.detector.width),
            "last_drift_timestamp": self.last_drift_timestamp.isoformat() if self.last_drift_timestamp else None,
        }

