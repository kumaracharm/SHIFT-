"""
DRIFTGUARD Real-Time Prediction Service
Executes concurrent supervised fraud probability estimation and unsupervised anomaly scoring.
"""

from typing import Dict, Tuple, Optional
import numpy as np
from models.fraud_classifier import SupervisedFraudClassifier
from models.anomaly_detector import StreamingAnomalyDetector


class PredictionService:
    """
    Coordinates model inference for streaming transactions:
    1. Computes supervised fraud probability via Random Forest.
    2. Computes streaming anomaly score via River HalfSpaceTrees.
    """

    def __init__(
        self,
        fraud_classifier: Optional[SupervisedFraudClassifier] = None,
        anomaly_detector: Optional[StreamingAnomalyDetector] = None,
    ):
        self.fraud_classifier = fraud_classifier or SupervisedFraudClassifier()
        self.anomaly_detector = anomaly_detector or StreamingAnomalyDetector()

    def predict(
        self,
        features_dict: Dict[str, float],
        features_vector: np.ndarray,
    ) -> Tuple[float, float, str]:
        """
        Executes prediction pipeline.
        Returns: (fraud_probability, anomaly_score, model_version_string)
        """
        # 1. Supervised probability
        fraud_prob = float(self.fraud_classifier.predict_proba(features_vector)[0])

        # 2. Streaming anomaly score (score before learn to prevent self-contamination)
        anomaly_score, _ = self.anomaly_detector.process_one(features_dict)

        model_version = self.fraud_classifier.version_id

        return round(fraud_prob, 4), round(anomaly_score, 4), model_version

