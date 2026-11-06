"""
DRIFTGUARD Anomaly Detectors
Implements:
1. River HalfSpaceTrees streaming anomaly detector with warm-up phase, streaming state, and normalized scores.
2. Scikit-learn IsolationForest offline baseline for offline benchmark comparisons.

CRITICAL ARCHITECTURAL PRINCIPLE:
Anomaly scores reflect statistical unexpectedness in the streaming data distribution.
They are NOT calibrated fraud probabilities and must never be conflated with supervised fraud likelihood.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from river.anomaly import HalfSpaceTrees
from sklearn.ensemble import IsolationForest
from config import settings


class StreamingAnomalyDetector:
    """
    Streaming unsupervised anomaly detector based on River HalfSpaceTrees.
    Learns incrementally from streaming observations, maintaining sliding window mass estimates.
    Score direction: higher values [0.0, 1.0] indicate higher statistical anomaly.
    """

    def __init__(
        self,
        feature_names: Optional[List[str]] = None,
        n_trees: int = settings.HST_N_TREES,
        height: int = settings.HST_HEIGHT,
        window_size: int = settings.HST_WINDOW_SIZE,
        seed: int = settings.HST_SEED,
        threshold: float = settings.HST_ANOMALY_THRESHOLD,
    ):
        self.feature_names = feature_names or [
            "amount",
            "log_amount",
            "amount_zscore",
            "time_since_prev",
            "transaction_velocity",
            "device_consistency",
            "session_consistency",
            "network_risk_flag",
        ]
        self.window_size = window_size
        self.threshold = threshold
        self.observation_count = 0

        # Feature limits to provide stable split ranges for HalfSpaceTrees
        self.limits: Dict[str, Tuple[float, float]] = {
            "amount": (0.0, 5000.0),
            "log_amount": (0.0, 10.0),
            "amount_zscore": (-10.0, 10.0),
            "time_since_prev": (0.0, 7200.0),
            "transaction_velocity": (0.0, 30.0),
            "device_consistency": (0.0, 1.0),
            "session_consistency": (0.0, 1.0),
            "network_risk_flag": (0.0, 1.0),
        }

        self.hst = HalfSpaceTrees(
            n_trees=n_trees,
            height=height,
            window_size=window_size,
            limits=self.limits,
            seed=seed,
        )

    def _filter_features(self, feat_dict: Dict[str, float]) -> Dict[str, float]:
        """Filters to designated features and clips to safe limits."""
        clean = {}
        for k in self.feature_names:
            val = float(feat_dict.get(k, 0.0))
            if k in self.limits:
                low, high = self.limits[k]
                val = float(np.clip(val, low, high))
            clean[k] = val
        return clean

    def score_one(self, feat_dict: Dict[str, float]) -> float:
        """
        Calculates anomaly score for an observation.
        Returns a float in [0.0, 1.0], where 1.0 indicates maximum anomaly.
        """
        filtered = self._filter_features(feat_dict)
        raw_score = self.hst.score_one(filtered)

        # During warm-up phase (before first window is full), return moderate baseline
        if self.observation_count < self.window_size:
            # Dampen score slightly during warm-up
            return float(np.clip(raw_score * 0.5, 0.0, 1.0))

        return float(np.clip(raw_score, 0.0, 1.0))

    def learn_one(self, feat_dict: Dict[str, float]) -> None:
        """Updates internal tree state with the new observation."""
        filtered = self._filter_features(feat_dict)
        self.hst.learn_one(filtered)
        self.observation_count += 1

    def process_one(self, feat_dict: Dict[str, float]) -> Tuple[float, bool]:
        """
        Scores first (no future leakage), then updates the streaming tree state.
        Returns: (anomaly_score, is_anomalous_flag)
        """
        score = self.score_one(feat_dict)
        self.learn_one(feat_dict)
        is_anom = score >= self.threshold
        return score, is_anom


class IsolationForestBaseline:
    """
    Offline unsupervised benchmark detector.
    Used for comparative evaluation against the streaming HalfSpaceTrees detector.
    """

    def __init__(
        self,
        contamination: float = 0.02,
        random_state: int = settings.RF_RANDOM_STATE,
    ):
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1,
        )
        self.is_fitted = False

    def fit(self, X: np.ndarray) -> None:
        """Fits Isolation Forest on historical feature matrix."""
        self.model.fit(X)
        self.is_fitted = True

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """
        Calculates normalized anomaly scores where 1.0 is most anomalous.
        Converts sklearn offset score into normalized [0, 1] range.
        """
        if not self.is_fitted:
            return np.full(shape=(X.shape[0] if X.ndim > 1 else 1,), fill_value=0.1, dtype=np.float32)

        if X.ndim == 1:
            X = X.reshape(1, -1)

        # In sklearn, lower score = more anomalous. Negative scores are outliers.
        raw_scores = self.model.score_samples(X)
        # Rescale: raw_scores typically range from -0.8 to -0.3. Normalize to [0, 1].
        normalized = np.clip(1.0 - (raw_scores + 0.8) / 0.5, 0.0, 1.0)
        return normalized.astype(np.float32)

