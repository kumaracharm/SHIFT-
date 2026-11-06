"""
DRIFTGUARD Transaction Feature Extractor
Extracts statistical and temporal metrics: amounts, log-transforms, deviations, and rolling velocities.
"""

from collections import deque
from typing import Dict, Any, Deque, Optional
import numpy as np
from ingestion.event_schema import TransactionEvent


class TransactionFeatureExtractor:
    """
    Computes statistical and velocity features on bounded rolling event histories.
    Guarantees no future leakage by evaluating against historical state strictly prior to current update.
    """

    def __init__(self, history_maxlen: int = 500):
        # account/device -> deque of historical amounts
        self._amount_history: Dict[str, Deque[float]] = {}
        # account/device -> last seen timestamp in epoch seconds
        self._last_seen_epoch: Dict[str, float] = {}
        # account/device -> deque of timestamps in epoch seconds
        self._timestamp_history: Dict[str, Deque[float]] = {}
        self.history_maxlen = history_maxlen

    def extract_features(self, event: TransactionEvent) -> Dict[str, float]:
        """Calculates transaction features for the given event."""
        key = event.device_id
        current_epoch = event.timestamp.timestamp()
        amount = float(event.amount)

        # 1. Base amount & log amount
        log_amount = float(np.log1p(amount))

        # 2. Time since previous transaction for this device/entity
        last_epoch = self._last_seen_epoch.get(key)
        if last_epoch is not None:
            time_since_prev = max(0.0, current_epoch - last_epoch)
        else:
            time_since_prev = 3600.0  # Default 1 hour if first time seen

        # 3. Rolling velocity (events in the last 60 seconds)
        timestamps = self._timestamp_history.get(key)
        if timestamps:
            # Count events within the last 60 seconds
            cutoff = current_epoch - 60.0
            rolling_velocity = sum(1.0 for t in timestamps if t >= cutoff) + 1.0
        else:
            rolling_velocity = float(event.transaction_velocity or 1.0)

        # 4. Amount z-score and deviation relative to rolling history
        amounts = self._amount_history.get(key)
        if amounts and len(amounts) >= 3:
            hist_mean = float(np.mean(amounts))
            hist_std = float(np.std(amounts))
            if hist_std > 1e-4:
                amount_zscore = float(np.clip((amount - hist_mean) / hist_std, -10.0, 10.0))
            else:
                amount_zscore = 0.0
            amount_deviation = float(abs(amount - hist_mean))
        else:
            amount_zscore = 0.0
            amount_deviation = 0.0

        # Update bounded historical state
        if key not in self._amount_history:
            self._amount_history[key] = deque(maxlen=self.history_maxlen)
            self._timestamp_history[key] = deque(maxlen=self.history_maxlen)

        self._amount_history[key].append(amount)
        self._timestamp_history[key].append(current_epoch)
        self._last_seen_epoch[key] = current_epoch

        return {
            "amount": amount,
            "log_amount": log_amount,
            "amount_zscore": amount_zscore,
            "amount_deviation": amount_deviation,
            "time_since_prev": time_since_prev,
            "transaction_velocity": rolling_velocity,
        }

