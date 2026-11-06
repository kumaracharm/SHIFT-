"""
DRIFTGUARD Evidence Engine
Compiles transparent, human-readable audit evidence justifying risk ratings and security rejections.
Adheres strictly to calculated metrics without hallucinating feature contributions.
"""

from typing import List, Dict, Any, Optional
from config import settings


class EvidenceEngine:
    """
    Translates model metrics, cryptographic verification logs, and telemetry signals
    into structured, auditable evidence items.
    """

    @staticmethod
    def generate_evidence(
        integrity_status: str,
        integrity_reason: str,
        fraud_prob: float,
        anomaly_score: float,
        context_risk: float,
        features_dict: Dict[str, float],
        data_drift_status: str = "STABLE",
        concept_drift_status: str = "STABLE",
    ) -> List[Dict[str, Any]]:
        evidence: List[Dict[str, Any]] = []

        # 1. Integrity Evidence
        if integrity_status != "VALID":
            evidence.append({
                "factor": "CRYPTOGRAPHIC_INTEGRITY",
                "severity": "CRITICAL",
                "detail": f"Event failed security verification: {integrity_reason} (status={integrity_status})",
            })
            return evidence  # For integrity failures, no ML evaluation was performed

        # 2. Supervised Fraud Likelihood Evidence
        if fraud_prob >= settings.THRESHOLD_HIGH_RISK:
            evidence.append({
                "factor": "SUPERVISED_FRAUD_PROBABILITY",
                "severity": "HIGH",
                "detail": f"Supervised classifier estimated high fraud probability of {fraud_prob:.1%}.",
            })
        elif fraud_prob >= settings.THRESHOLD_REVIEW:
            evidence.append({
                "factor": "SUPERVISED_FRAUD_PROBABILITY",
                "severity": "MEDIUM",
                "detail": f"Supervised classifier estimated moderate fraud probability of {fraud_prob:.1%}.",
            })

        # 3. Streaming Anomaly Evidence
        if anomaly_score >= settings.HST_ANOMALY_THRESHOLD:
            evidence.append({
                "factor": "STREAMING_ANOMALY",
                "severity": "MEDIUM",
                "detail": f"HalfSpaceTrees anomaly score {anomaly_score:.2f} exceeded baseline threshold {settings.HST_ANOMALY_THRESHOLD:.2f}.",
            })

        # 4. Contextual & Behavioral Telemetry Evidence
        amount = features_dict.get("amount", 0.0)
        zscore = features_dict.get("amount_zscore", 0.0)
        if abs(zscore) >= settings.AMOUNT_ZSCORE_WARNING:
            evidence.append({
                "factor": "UNUSUAL_AMOUNT",
                "severity": "HIGH" if abs(zscore) >= 5.0 else "MEDIUM",
                "detail": f"Transaction amount ${amount:.2f} has z-score deviation of {zscore:.1f}σ relative to device history.",
            })

        velocity = features_dict.get("transaction_velocity", 1.0)
        if velocity >= settings.VELOCITY_WARNING_COUNT:
            evidence.append({
                "factor": "VELOCITY_SPIKE",
                "severity": "MEDIUM",
                "detail": f"Rapid velocity burst: {velocity:.0f} transactions recorded in short rolling window.",
            })

        dev_cons = features_dict.get("device_consistency", 1.0)
        if dev_cons < 0.5:
            evidence.append({
                "factor": "DEVICE_MISMATCH",
                "severity": "MEDIUM",
                "detail": "Session originated from an unrecognized hardware device/browser fingerprint.",
            })

        net_risk = features_dict.get("network_risk_flag", 0.0)
        if net_risk > 0.5:
            evidence.append({
                "factor": "NETWORK_RISK",
                "severity": "MEDIUM",
                "detail": "Connection telemetry identified unexpected ASN change or anonymous VPN/proxy exit node.",
            })

        # 5. Drift Telemetry Awareness (Independent stream health dimension)
        if data_drift_status == "DRIFT_DETECTED":
            evidence.append({
                "factor": "STREAM_HEALTH_DATA_DRIFT",
                "severity": "INFO",
                "detail": "ADWIN detector identified statistical shift in streaming anomaly distribution.",
            })

        if concept_drift_status == "CONCEPT_DRIFT_DETECTED":
            evidence.append({
                "factor": "STREAM_HEALTH_CONCEPT_DRIFT",
                "severity": "WARNING",
                "detail": "ADWIN detector flagged shift in verified label prediction errors; model retraining advised.",
            })

        if not evidence:
            evidence.append({
                "factor": "BASELINE_NORMAL",
                "severity": "LOW",
                "detail": "Transaction parameters conform to typical statistical baseline.",
            })

        return evidence

