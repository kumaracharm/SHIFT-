"""
DRIFTGUARD Context Risk Engine
Evaluates contextual, session, and network telemetry indicators into a normalized [0.0, 1.0] risk score.
"""

from typing import Dict, Any


class ContextRiskEngine:
    """
    Computes deterministic context risk from verified telemetry:
    - Device continuity
    - Session stability
    - Network / VPN risk indicators
    - Velocity anomalies
    """

    @staticmethod
    def evaluate_context_risk(features_dict: Dict[str, float]) -> float:
        """
        Calculates context risk score in [0.0, 1.0].
        Combines observable physical attributes without guessing unobserved data.
        """
        score = 0.0

        # Device inconsistency penalty
        dev_cons = float(features_dict.get("device_consistency", 1.0))
        if dev_cons < 0.5:
            score += 0.40

        # Network / VPN risk penalty
        net_risk = float(features_dict.get("network_risk_flag", 0.0))
        if net_risk > 0.5:
            score += 0.35

        # Session inconsistency
        sess_cons = float(features_dict.get("session_consistency", 1.0))
        if sess_cons < 0.6:
            score += 0.15

        # Excessive transaction velocity
        velocity = float(features_dict.get("transaction_velocity", 1.0))
        if velocity >= 5.0:
            score += 0.30
        elif velocity >= 3.0:
            score += 0.15

        # Clamp between 0.0 and 1.0
        return round(min(1.0, max(0.0, score)), 4)

