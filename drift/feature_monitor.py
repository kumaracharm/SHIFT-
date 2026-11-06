"""
DRIFTGUARD Feature Distribution Drift Monitor (PSI)
Computes Population Stability Index (PSI) across streaming feature windows
to detect feature-level covariates shifts without needing ground-truth labels.
"""

from collections import deque
from typing import Dict, List, Optional, Tuple, Deque
import numpy as np
from config import settings


class FeatureDistributionMonitor:
    """
    Maintains a reference baseline window and a sliding operational window.
    Computes Population Stability Index (PSI) for each feature dimension.
    """

    def __init__(
        self,
        feature_names: Optional[List[str]] = None,
        reference_window_size: int = settings.PSI_REFERENCE_WINDOW_SIZE,
        stream_window_size: int = settings.PSI_STREAM_WINDOW_SIZE,
        moderate_threshold: float = settings.PSI_THRESHOLD_MODERATE,
        high_threshold: float = settings.PSI_THRESHOLD_HIGH,
    ):
        self.feature_names = feature_names or [
            "amount",
            "log_amount",
            "transaction_velocity",
            "time_since_prev",
        ]
        self.ref_size = reference_window_size
        self.stream_size = stream_window_size
        self.moderate_threshold = moderate_threshold
        self.high_threshold = high_threshold

        # Sliding buffers for each feature
        self.reference_buffers: Dict[str, Deque[float]] = {
            f: deque(maxlen=reference_window_size) for f in self.feature_names
        }
        self.stream_buffers: Dict[str, Deque[float]] = {
            f: deque(maxlen=stream_window_size) for f in self.feature_names
        }
        self.reference_frozen: bool = False

    def freeze_reference(self) -> None:
        """Locks the reference baseline buffers so future stream updates only populate operational buffers."""
        self.reference_frozen = True
        for b in self.stream_buffers.values():
            b.clear()

    def unfreeze_reference(self) -> None:
        """Unlocks the reference baseline buffers."""
        self.reference_frozen = False

    def seed_reference(self, baseline_df_or_dict: Dict[str, List[float]]) -> None:
        """Initializes the reference baseline distribution with historical training data."""
        for feat, vals in baseline_df_or_dict.items():
            if feat in self.reference_buffers:
                for v in vals:
                    self.reference_buffers[feat].append(float(v))

    def update(self, features_dict: Dict[str, float]) -> None:
        """Appends streaming observation to recent operational window."""
        for feat in self.feature_names:
            if feat in features_dict:
                val = float(features_dict[feat])
                # If reference isn't frozen, populate reference
                if not self.reference_frozen and len(self.reference_buffers[feat]) < self.ref_size:
                    self.reference_buffers[feat].append(val)
                self.stream_buffers[feat].append(val)

    def calculate_psi_for_feature(
        self,
        feature_name: str,
        num_bins: Optional[int] = None,
        epsilon: float = 1e-4,
    ) -> Tuple[float, str]:
        """
        Calculates Population Stability Index between reference and current stream buffer.
        Returns: (psi_value, status_category)
        """
        ref_data = np.array(self.reference_buffers[feature_name], dtype=np.float64)
        curr_data = np.array(self.stream_buffers[feature_name], dtype=np.float64)

        if len(ref_data) < 20 or len(curr_data) < 20:
            return 0.0, "INSUFFICIENT_DATA"

        # Adaptive bin count: 5 bins for small streaming windows (< 500) to prevent small-sample noise
        bins = num_bins or (5 if len(curr_data) < 500 else 10)

        # Calculate quantile bin edges from reference distribution
        quantiles = np.linspace(0, 100, bins + 1)
        bin_edges = np.percentile(ref_data, quantiles)
        bin_edges[0] = -np.inf
        bin_edges[-1] = np.inf
        bin_edges = np.unique(bin_edges)  # handle tied quantiles

        # Bin counts
        ref_counts, _ = np.histogram(ref_data, bins=bin_edges)
        curr_counts, _ = np.histogram(curr_data, bins=bin_edges)

        # Proportions with Laplace smoothing
        ref_props = (ref_counts + epsilon) / (len(ref_data) + epsilon * len(ref_counts))
        curr_props = (curr_counts + epsilon) / (len(curr_data) + epsilon * len(curr_counts))

        # PSI sum
        psi_contributions = (curr_props - ref_props) * np.log(curr_props / ref_props)
        psi = float(np.sum(psi_contributions))

        if psi > self.high_threshold:
            status = "SIGNIFICANT_DRIFT"
        elif psi >= self.moderate_threshold:
            status = "MODERATE_DRIFT"
        else:
            status = "STABLE"

        return round(psi, 4), status

    def evaluate_all(self) -> Dict[str, Dict[str, Any]]:
        """Evaluates PSI across all registered features."""
        results = {}
        for feat in self.feature_names:
            psi_val, status = self.calculate_psi_for_feature(feat)
            results[feat] = {
                "psi": psi_val,
                "status": status,
                "ref_samples": len(self.reference_buffers[feat]),
                "stream_samples": len(self.stream_buffers[feat]),
            }
        return results
