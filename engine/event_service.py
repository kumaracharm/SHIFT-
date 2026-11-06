"""
DRIFTGUARD Central Event Processing Service
Primary architectural orchestrator implementing the end-to-end module contract:
1. Ingests and validates transaction event.
2. Cryptographically verifies Ed25519 signature, freshness window, and SQLite replay state.
3. If integrity fails: stops untrusted execution immediately, logs audit record, and returns INTEGRITY_REJECTED.
4. Extracts streaming transaction and context features without future leakage.
5. Executes supervised Random Forest classifier and River HalfSpaceTrees anomaly detector.
6. Updates ADWIN unlabelled drift monitor and PSI feature distributions.
7. Evaluates context risk and generates human-readable evidence.
8. Decides final risk rating (NORMAL, MONITOR, REVIEW, HIGH_RISK).
9. Atomically persists event, prediction, and telemetry in SQLite.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from config import settings
from ingestion.event_schema import TransactionEvent
from security.key_manager import KeyManager
from security.integrity_service import IntegrityService
from features.feature_pipeline import FeaturePipeline
from models.prediction_service import PredictionService
from drift.drift_manager import DriftManager
from engine.risk_engine import ContextRiskEngine
from engine.evidence_engine import EvidenceEngine
from engine.decision_engine import DecisionEngine
from engine.risk_fusion import RiskFusionEngine
from models.experts.specialists import SupervisedFraudExpert, BehaviouralAnomalyExpert
from storage.repositories import EventRepository, PredictionRepository


@dataclass
class ProcessingResult:
    """Standardized output structure for processed transaction events."""
    event_id: str
    integrity_status: str
    fraud_probability: float
    anomaly_score: float
    context_risk: float
    data_drift_status: str
    labelled_error_drift_status: str
    decision: str
    evidence: List[Dict[str, Any]]
    model_version: str
    processing_timestamp: datetime
    expert_fusion: Optional[Dict[str, Any]] = None


class EventProcessingService:
    """Central processing pipeline."""

    def __init__(
        self,
        session: Session,
        key_manager: Optional[KeyManager] = None,
        prediction_service: Optional[PredictionService] = None,
        drift_manager: Optional[DriftManager] = None,
        feature_pipeline: Optional[FeaturePipeline] = None,
        risk_fusion: Optional[RiskFusionEngine] = None,
        enforce_freshness: bool = True,
    ):
        self.session = session
        self.key_manager = key_manager or KeyManager()
        self.integrity_service = IntegrityService(
            session=session,
            key_manager=self.key_manager,
            enforce_freshness=enforce_freshness,
        )
        self.feature_pipeline = feature_pipeline or FeaturePipeline()
        self.prediction_service = prediction_service or PredictionService()
        self.drift_manager = drift_manager or DriftManager(session=session)
        self.risk_fusion = risk_fusion or RiskFusionEngine(
            supervised_expert=SupervisedFraudExpert(classifier=self.prediction_service.fraud_classifier),
            behavioural_expert=BehaviouralAnomalyExpert(detector=self.prediction_service.anomaly_detector),
        )
        self.event_repo = EventRepository(session=session)
        self.prediction_repo = PredictionRepository(session=session)

    def process_event(
        self,
        event: TransactionEvent,
        client_ip: Optional[str] = None,
        reference_time: Optional[datetime] = None,
    ) -> ProcessingResult:
        now = datetime.now(timezone.utc)

        # 1. Cryptographic and Replay Integrity Verification
        integrity_res = self.integrity_service.verify_event(
            event=event,
            client_ip=client_ip,
            reference_time=reference_time,
        )

        if not integrity_res.is_valid:
            # STOP: Do not execute trusted ML pipeline on invalid or replayed payload
            evidence = EvidenceEngine.generate_evidence(
                integrity_status=integrity_res.status,
                integrity_reason=integrity_res.reason,
                fraud_prob=0.0,
                anomaly_score=0.0,
                context_risk=1.0,
                features_dict={},
            )
            decision = DecisionEngine.evaluate(
                integrity_status=integrity_res.status,
                fraud_prob=0.0,
                anomaly_score=0.0,
                context_risk=1.0,
            )

            result = ProcessingResult(
                event_id=event.event_id,
                integrity_status=integrity_res.status,
                fraud_probability=0.0,
                anomaly_score=0.0,
                context_risk=1.0,
                data_drift_status="UNCHECKED",
                labelled_error_drift_status="UNCHECKED",
                decision=decision,
                evidence=evidence,
                model_version=self.prediction_service.fraud_classifier.version_id,
                processing_timestamp=now,
            )
            return result

        # 2. Extract Streaming Features
        features_dict, features_vector = self.feature_pipeline.extract_features(event)

        # 3. Model Inference (Supervised Fraud Probability + Streaming HalfSpaceTrees Anomaly)
        fraud_prob, anomaly_score, model_version = self.prediction_service.predict(
            features_dict=features_dict,
            features_vector=features_vector,
        )

        # 4. Drift Monitoring
        _, data_drift_status, _ = self.drift_manager.observe_unlabelled_signal(
            anomaly_score=anomaly_score,
            timestamp=event.timestamp,
        )
        self.drift_manager.observe_features(features_dict)
        labelled_status = self.drift_manager.last_labelled_status

        # 5. Context Risk Evaluation
        context_risk = ContextRiskEngine.evaluate_context_risk(features_dict)

        # 5b. Multi-Expert Risk Fusion Evaluation
        expert_fusion = self.risk_fusion.evaluate(
            event_dict=event.model_dump(mode="json"),
            features_dict=features_dict,
            context={"features_vector": features_vector},
        )

        # 6. Evidence Generation
        evidence = EvidenceEngine.generate_evidence(
            integrity_status="VALID",
            integrity_reason="Signature and freshness verified.",
            fraud_prob=fraud_prob,
            anomaly_score=anomaly_score,
            context_risk=context_risk,
            features_dict=features_dict,
            data_drift_status=data_drift_status,
            concept_drift_status=labelled_status,
        )

        # Attach multi-expert synthesis into evidence
        evidence.append({
            "factor": "MULTI_EXPERT_FUSION",
            "severity": "HIGH" if expert_fusion["consensus_action"] == "BLOCK" else ("MEDIUM" if expert_fusion["consensus_action"] == "REVIEW" else "LOW"),
            "detail": f"7-Specialist Consensus: {expert_fusion['consensus_action']} (Risk: {expert_fusion['fused_risk_score']:.1%}, Confidence: {expert_fusion['fused_confidence']:.1%}).",
            "fusion": expert_fusion,
        })

        # 7. Decision Evaluation
        decision = DecisionEngine.evaluate(
            integrity_status="VALID",
            fraud_prob=fraud_prob,
            anomaly_score=anomaly_score,
            context_risk=context_risk,
        )

        # 8. Persist Event and Prediction in SQLite
        event_dict = {
            "event_id": event.event_id,
            "transaction_id": event.transaction_id,
            "timestamp": event.timestamp,
            "device_id": event.device_id,
            "session_id": event.session_id,
            "key_id": event.key_id,
            "nonce": event.nonce,
            "amount": event.amount,
            "signature": event.signature,
            "payload_json": event.model_dump(mode="json"),
        }
        self.event_repo.save_event(event_dict, commit=False)

        pred_dict = {
            "event_id": event.event_id,
            "fraud_probability": fraud_prob,
            "anomaly_score": anomaly_score,
            "context_risk": context_risk,
            "decision": decision,
            "evidence": evidence,
            "model_version": model_version,
            "processing_timestamp": now,
        }
        self.prediction_repo.save_prediction(pred_dict, commit=True)

        return ProcessingResult(
            event_id=event.event_id,
            integrity_status="VALID",
            fraud_probability=fraud_prob,
            anomaly_score=anomaly_score,
            context_risk=context_risk,
            data_drift_status=data_drift_status,
            labelled_error_drift_status=labelled_status,
            decision=decision,
            evidence=evidence,
            model_version=model_version,
            processing_timestamp=now,
            expert_fusion=expert_fusion,
        )

