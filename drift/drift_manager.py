"""
DRIFTGUARD Drift Manager
Unified orchestration for streaming data drift, concept drift, and covariate shifts.
Persists drift alert events to SQLite and provides telemetry snapshots for downstream services.

ARCHITECTURAL PRINCIPLES:
1. Data drift is statistical variation in input distributions; it is NOT automatically concept drift.
2. Concept drift represents changes in P(Y|X) and requires verified ground-truth label feedback.
3. Drift detection alerts telemetry health; it NEVER automatically inflates transaction fraud risk.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from drift.adwin_monitor import ADWINChannelMonitor, ADWINSignalType
from drift.feature_monitor import FeatureDistributionMonitor
from storage.repositories import DriftRepository


class DriftManager:
    """
    Coordinates multi-channel drift monitoring across:
    - Unlabelled streaming anomaly signals (ADWIN)
    - Labelled prediction error signals (ADWIN)
    - Feature distribution stability (PSI)
    """

    def __init__(self, session: Session):
        self.session = session
        self.repo = DriftRepository(session)

        # ADWIN Monitors
        self.adwin_unlabelled = ADWINChannelMonitor(
            signal_type=ADWINSignalType.UNLABELLED_ANOMALY
        )
        self.adwin_labelled = ADWINChannelMonitor(
            signal_type=ADWINSignalType.LABELLED_ERROR
        )

        # PSI Feature Monitor
        self.feature_monitor = FeatureDistributionMonitor()

        # Cached telemetry state
        self.last_unlabelled_status = "STABLE"
        self.last_labelled_status = "STABLE"

    def observe_unlabelled_signal(
        self,
        anomaly_score: float,
        timestamp: Optional[datetime] = None,
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Updates unlabelled ADWIN detector with the streaming anomaly score.
        Persists record if drift is detected.
        """
        ts = timestamp or datetime.now(timezone.utc)
        drift_detected, details = self.adwin_unlabelled.update(anomaly_score, timestamp=ts)

        if drift_detected:
            self.last_unlabelled_status = "DRIFT_DETECTED"
            self.repo.save_drift_event(
                detector_name="ADWIN_Unlabelled",
                signal_type=ADWINSignalType.UNLABELLED_ANOMALY,
                timestamp=ts,
                observation_count=self.adwin_unlabelled.observation_count,
                metric_value=anomaly_score,
                details=details,
            )
        else:
            self.last_unlabelled_status = "STABLE"

        return drift_detected, self.last_unlabelled_status, details

    def observe_ground_truth(
        self,
        y_true: int,
        predicted_prob: float,
        timestamp: Optional[datetime] = None,
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Updates labelled ADWIN detector with prediction residual error |y_true - y_pred|.
        True concept drift is flagged when verified classification errors shift statistically.
        """
        ts = timestamp or datetime.now(timezone.utc)
        error = abs(float(y_true) - float(predicted_prob))
        drift_detected, details = self.adwin_labelled.update(error, timestamp=ts)
        details["error"] = round(error, 4)
        details["y_true"] = y_true
        details["predicted_prob"] = predicted_prob

        if drift_detected:
            self.last_labelled_status = "CONCEPT_DRIFT_DETECTED"
            self.repo.save_drift_event(
                detector_name="ADWIN_Labelled_Error",
                signal_type=ADWINSignalType.LABELLED_ERROR,
                timestamp=ts,
                observation_count=self.adwin_labelled.observation_count,
                metric_value=error,
                details=details,
            )
        else:
            self.last_labelled_status = "STABLE"

        return drift_detected, self.last_labelled_status, details

    def observe_features(self, features_dict: Dict[str, float]) -> None:
        """Updates rolling buffers for PSI feature distribution tracking."""
        self.feature_monitor.update(features_dict)

    def freeze_reference(self) -> None:
        """Locks the baseline reference distributions for all monitored features."""
        self.feature_monitor.freeze_reference()

    def unfreeze_reference(self) -> None:
        """Unlocks the baseline reference distributions."""
        self.feature_monitor.unfreeze_reference()

    def get_summary_status(self) -> Dict[str, Any]:
        """Provides an operational telemetry snapshot of all drift channels."""
        psi_report = self.feature_monitor.evaluate_all()
        return {
            "unlabelled_anomaly_drift": self.last_unlabelled_status,
            "labelled_concept_drift": self.last_labelled_status,
            "unlabelled_adwin_observations": self.adwin_unlabelled.observation_count,
            "labelled_adwin_observations": self.adwin_labelled.observation_count,
            "psi_features": psi_report,
        }

