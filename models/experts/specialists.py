"""
DRIFTGUARD 2.0 Specialist Detection Experts
Implements the 7 specialist models powering multi-expert detection.
"""

from typing import Dict, Any, List, Optional
import numpy as np

from models.experts.base_expert import BaseExpert, ExpertResult
from models.fraud_classifier import SupervisedFraudClassifier
from models.anomaly_detector import StreamingAnomalyDetector, IsolationForestBaseline
from config import settings


class SupervisedFraudExpert(BaseExpert):
    """Expert 1: Supervised Fraud Classifier (IEEE-CIS Random Forest)."""

    def __init__(self, classifier: Optional[SupervisedFraudClassifier] = None, weight: float = 2.0):
        super().__init__(name="Supervised Fraud Expert", category="ML_SUPERVISED", default_weight=weight)
        self.classifier = classifier or SupervisedFraudClassifier()

    def evaluate(
        self,
        event_dict: Dict[str, Any],
        features_dict: Dict[str, float],
        context: Optional[Dict[str, Any]] = None,
    ) -> ExpertResult:
        feat_vector = context.get("features_vector") if context else None
        if feat_vector is None:
            # Fallback construct 8-feature vector from dictionary
            keys = [
                "amount", "log_amount", "amount_zscore", "time_since_prev",
                "transaction_velocity", "device_consistency", "session_consistency", "network_risk_flag"
            ]
            feat_vector = np.array([[features_dict.get(k, 0.0) for k in keys]], dtype=np.float32)

        fraud_prob = float(self.classifier.predict_proba(feat_vector)[0])
        reasons = []
        if fraud_prob >= settings.THRESHOLD_HIGH_RISK:
            decision = "BLOCK"
            reasons.append(f"Supervised model predicted high fraud risk ({fraud_prob:.1%}) exceeding threshold {settings.THRESHOLD_HIGH_RISK:.0%}")
        elif fraud_prob >= settings.THRESHOLD_REVIEW:
            decision = "REVIEW"
            reasons.append(f"Supervised model predicted elevated fraud likelihood ({fraud_prob:.1%})")
        else:
            decision = "ALLOW"
            reasons.append(f"Supervised model score ({fraud_prob:.1%}) within normal legitimate bounds")

        return ExpertResult(
            expert_name=self.name,
            category=self.category,
            score=fraud_prob,
            confidence=0.92,
            weight=self.weight,
            decision=decision,
            reasons=reasons,
            metadata={"model_version": self.classifier.version_id, "n_features": getattr(self.classifier.model, "n_features_in_", 8)},
        )


class BehaviouralAnomalyExpert(BaseExpert):
    """Expert 2: Streaming Half-Space Trees Behavioural Anomaly Detector."""

    def __init__(self, detector: Optional[StreamingAnomalyDetector] = None, weight: float = 1.5):
        super().__init__(name="Behavioural HST Expert", category="STREAMING_ANOMALY", default_weight=weight)
        self.detector = detector or StreamingAnomalyDetector()

    def evaluate(
        self,
        event_dict: Dict[str, Any],
        features_dict: Dict[str, float],
        context: Optional[Dict[str, Any]] = None,
    ) -> ExpertResult:
        score = self.detector.score_one(features_dict)
        self.detector.learn_one(features_dict)

        reasons = []
        if score >= 0.85:
            decision = "BLOCK"
            reasons.append(f"Severe streaming distribution anomaly ({score:.2f}) across behavioral subspace")
        elif score >= settings.HST_ANOMALY_THRESHOLD:
            decision = "REVIEW"
            reasons.append(f"Statistically atypical behavioral pattern ({score:.2f} >= {settings.HST_ANOMALY_THRESHOLD:.2f})")
        else:
            decision = "ALLOW"
            reasons.append(f"Behavior aligns with dynamic sliding window distribution ({score:.2f})")

        return ExpertResult(
            expert_name=self.name,
            category=self.category,
            score=score,
            confidence=0.85,
            weight=self.weight,
            decision=decision,
            reasons=reasons,
            metadata={"trees": settings.HST_N_TREES, "window": settings.HST_WINDOW_SIZE},
        )


class IsolationForestExpert(BaseExpert):
    """Expert 3: Isolation Forest Baseline Density Estimator."""

    def __init__(self, baseline: Optional[IsolationForestBaseline] = None, weight: float = 1.0):
        super().__init__(name="Isolation Forest Expert", category="OFFLINE_ANOMALY", default_weight=weight)
        self.baseline = baseline or IsolationForestBaseline()

    def evaluate(
        self,
        event_dict: Dict[str, Any],
        features_dict: Dict[str, float],
        context: Optional[Dict[str, Any]] = None,
    ) -> ExpertResult:
        feat_vector = context.get("features_vector") if context else None
        if feat_vector is None:
            keys = [
                "amount", "log_amount", "amount_zscore", "time_since_prev",
                "transaction_velocity", "device_consistency", "session_consistency", "network_risk_flag"
            ]
            feat_vector = np.array([[features_dict.get(k, 0.0) for k in keys]], dtype=np.float32)

        score = float(self.baseline.score_samples(feat_vector)[0])
        reasons = []
        if score >= 0.80:
            decision = "BLOCK"
            reasons.append(f"High isolation depth outlier score ({score:.2f})")
        elif score >= 0.55:
            decision = "REVIEW"
            reasons.append(f"Moderate subspace isolation outlier score ({score:.2f})")
        else:
            decision = "ALLOW"
            reasons.append("Dense cluster member, no isolation observed")

        return ExpertResult(
            expert_name=self.name,
            category=self.category,
            score=score,
            confidence=0.80,
            weight=self.weight,
            decision=decision,
            reasons=reasons,
            metadata={"is_fitted": self.baseline.is_fitted},
        )


class TransactionVelocityExpert(BaseExpert):
    """Expert 4: Velocity and Burst Frequency Specialist."""

    def __init__(self, weight: float = 1.3):
        super().__init__(name="Velocity & Burst Expert", category="VELOCITY_ANALYSIS", default_weight=weight)

    def evaluate(
        self,
        event_dict: Dict[str, Any],
        features_dict: Dict[str, float],
        context: Optional[Dict[str, Any]] = None,
    ) -> ExpertResult:
        velocity = float(features_dict.get("transaction_velocity", 1.0))
        time_since = float(features_dict.get("time_since_prev", 60.0))

        score = 0.0
        reasons = []

        if velocity >= 6.0:
            score += 0.85
            reasons.append(f"Extreme burst velocity: {velocity:.1f} tx/min detected")
        elif velocity >= 3.5:
            score += 0.55
            reasons.append(f"Elevated transaction velocity: {velocity:.1f} tx/min")
        elif velocity >= 2.0:
            score += 0.25

        if time_since < 2.0:
            score = max(score, 0.90)
            reasons.append(f"Sub-second or near-instant repeat transaction ({time_since:.1f}s)")
        elif time_since < 5.0:
            score = max(score, 0.60)
            reasons.append(f"Rapid succession transaction interval ({time_since:.1f}s)")

        score = min(1.0, score)
        if score >= 0.70:
            decision = "BLOCK"
        elif score >= 0.40:
            decision = "REVIEW"
        else:
            decision = "ALLOW"
            reasons.append("Normal transaction velocity and pacing intervals")

        return ExpertResult(
            expert_name=self.name,
            category=self.category,
            score=score,
            confidence=0.90,
            weight=self.weight,
            decision=decision,
            reasons=reasons,
            metadata={"velocity": velocity, "time_since_prev": time_since},
        )


class DeviceSessionExpert(BaseExpert):
    """Expert 5: Device Fingerprint & Session Continuity Specialist."""

    def __init__(self, weight: float = 1.2):
        super().__init__(name="Device & Session Expert", category="DEVICE_CONTINUITY", default_weight=weight)

    def evaluate(
        self,
        event_dict: Dict[str, Any],
        features_dict: Dict[str, float],
        context: Optional[Dict[str, Any]] = None,
    ) -> ExpertResult:
        dev_cons = float(features_dict.get("device_consistency", 1.0))
        sess_cons = float(features_dict.get("session_consistency", 1.0))

        score = 0.0
        reasons = []

        if dev_cons < 0.3:
            score += 0.65
            reasons.append(f"Severe device fingerprint discontinuity ({dev_cons:.2f})")
        elif dev_cons < 0.7:
            score += 0.35
            reasons.append(f"Unfamiliar device signature ({dev_cons:.2f})")

        if sess_cons < 0.4:
            score += 0.35
            reasons.append(f"Session hijack or multi-session collision indicator ({sess_cons:.2f})")
        elif sess_cons < 0.8:
            score += 0.15

        score = min(1.0, score)
        if score >= 0.70:
            decision = "BLOCK"
        elif score >= 0.40:
            decision = "REVIEW"
        else:
            decision = "ALLOW"
            reasons.append("Authenticated device and consistent active session")

        return ExpertResult(
            expert_name=self.name,
            category=self.category,
            score=score,
            confidence=0.88,
            weight=self.weight,
            decision=decision,
            reasons=reasons,
            metadata={"device_consistency": dev_cons, "session_consistency": sess_cons},
        )


class NetworkRiskExpert(BaseExpert):
    """Expert 6: IP Reputation, Geolocation & Network Infrastructure Specialist."""

    def __init__(self, weight: float = 1.1):
        super().__init__(name="Network Risk Expert", category="NETWORK_SECURITY", default_weight=weight)

    def evaluate(
        self,
        event_dict: Dict[str, Any],
        features_dict: Dict[str, float],
        context: Optional[Dict[str, Any]] = None,
    ) -> ExpertResult:
        net_risk = float(features_dict.get("network_risk_flag", 0.0))
        score = 0.0
        reasons = []

        if net_risk >= 0.8:
            score = 0.85
            reasons.append("Connection originated from identified VPN, proxy, or high-risk hosting ASN")
        elif net_risk >= 0.4:
            score = 0.45
            reasons.append("Network telemetry exhibits suspicious routing or untrusted gateway")
        else:
            reasons.append("Clean residential / carrier IP routing verified")

        if score >= 0.70:
            decision = "BLOCK"
        elif score >= 0.40:
            decision = "REVIEW"
        else:
            decision = "ALLOW"

        return ExpertResult(
            expert_name=self.name,
            category=self.category,
            score=score,
            confidence=0.85,
            weight=self.weight,
            decision=decision,
            reasons=reasons,
            metadata={"network_risk_flag": net_risk},
        )


class RuleExpert(BaseExpert):
    """Expert 7: Deterministic Banking & UPI Business Rule Engine."""

    def __init__(self, weight: float = 1.8):
        super().__init__(name="Rule-Based Policy Expert", category="BUSINESS_RULES", default_weight=weight)

    def evaluate(
        self,
        event_dict: Dict[str, Any],
        features_dict: Dict[str, float],
        context: Optional[Dict[str, Any]] = None,
    ) -> ExpertResult:
        amount = float(event_dict.get("amount", features_dict.get("amount", 0.0)))
        amount_zscore = float(features_dict.get("amount_zscore", 0.0))
        score = 0.0
        reasons = []

        # Rule 1: Astronomical high-value UPI transfer (> ₹100,000)
        if amount >= 100000.0:
            score = max(score, 0.90)
            reasons.append(f"Rule TRIGGER: Transaction amount ₹{amount:,.2f} exceeds high-value threshold (₹100k)")
        elif amount >= 50000.0:
            score = max(score, 0.60)
            reasons.append(f"Rule TRIGGER: Transaction amount ₹{amount:,.2f} exceeds standard monitoring limit (₹50k)")

        # Rule 2: Extreme statistical z-score outlier (> 4 sigma)
        if amount_zscore >= 4.0:
            score = max(score, 0.85)
            reasons.append(f"Rule TRIGGER: Amount exceeds 4 standard deviations above user historical mean (+{amount_zscore:.1f}σ)")
        elif amount_zscore >= 2.5:
            score = max(score, 0.50)
            reasons.append(f"Rule TRIGGER: Unusual amount variance (+{amount_zscore:.1f}σ)")

        # Rule 3: Mule account flag in payload metadata
        payload = event_dict.get("payload_json") or {}
        if isinstance(payload, str):
            import json
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {}
        if payload.get("mule_ring_id") or "mule" in str(payload.get("receiver_id", "")).lower():
            score = max(score, 0.95)
            reasons.append("Rule TRIGGER: Receiver identified in active mule ring network")

        if score >= 0.75:
            decision = "BLOCK"
        elif score >= 0.45:
            decision = "REVIEW"
        else:
            decision = "ALLOW"
            reasons.append("All deterministic business policies and statutory limits satisfied")

        return ExpertResult(
            expert_name=self.name,
            category=self.category,
            score=score,
            confidence=1.0,  # Rules have 100% deterministic confidence
            weight=self.weight,
            decision=decision,
            reasons=reasons,
            metadata={"amount": amount, "amount_zscore": amount_zscore},
        )

