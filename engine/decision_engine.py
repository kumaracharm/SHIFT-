"""
DRIFTGUARD Decision Engine
Produces definitive risk classifications while maintaining strict dimensional independence
between transaction fraud risk, cryptographic integrity, and stream health.
"""

from typing import Tuple
from config import settings


class DecisionType:
    NORMAL = "NORMAL"
    MONITOR = "MONITOR"
    REVIEW = "REVIEW"
    HIGH_RISK = "HIGH_RISK"
    INTEGRITY_REJECTED = "INTEGRITY_REJECTED"

    ALLOW = "ALLOW"
    BLOCK = "BLOCK"

    @classmethod
    def to_action(cls, decision: str) -> str:
        if decision in (cls.NORMAL, cls.MONITOR, cls.ALLOW):
            return cls.ALLOW
        elif decision == cls.REVIEW:
            return cls.REVIEW
        return cls.BLOCK


class DecisionEngine:
    """
    Evaluates verified telemetry, fraud probabilities, and context risk against validation thresholds.
    """

    @staticmethod
    def evaluate(
        integrity_status: str,
        fraud_prob: float,
        anomaly_score: float,
        context_risk: float,
    ) -> str:
        """
        Determines the operational risk category.
        Enforces:
        - If integrity failed, decision is ALWAYS INTEGRITY_REJECTED.
        - Stream drift NEVER automatically elevates a normal transaction into HIGH_RISK.
        """
        if integrity_status != "VALID":
            return DecisionType.INTEGRITY_REJECTED

        # 1. High Risk Criteria
        if (
            fraud_prob >= settings.THRESHOLD_HIGH_RISK
            or (fraud_prob >= settings.THRESHOLD_REVIEW and context_risk >= 0.8)
        ):
            return DecisionType.HIGH_RISK

        # 2. Review Criteria
        if (
            fraud_prob >= settings.THRESHOLD_REVIEW
            or context_risk >= 0.60
            or anomaly_score >= 0.85
        ):
            return DecisionType.REVIEW

        # 3. Monitor Criteria
        if (
            fraud_prob >= settings.THRESHOLD_MONITOR
            or context_risk >= 0.30
            or anomaly_score >= settings.HST_ANOMALY_THRESHOLD
        ):
            return DecisionType.MONITOR

        # 4. Normal Baseline
        return DecisionType.NORMAL

