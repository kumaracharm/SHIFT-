"""
DRIFTGUARD 2.0 Multi-Expert Risk Fusion Engine
Combines evaluations from the 7 specialist detection experts using a transparent,
weighted consensus architecture with full explainability.
"""

from typing import Dict, Any, List, Optional
import numpy as np

from models.experts.base_expert import ExpertResult
from models.experts.specialists import (
    SupervisedFraudExpert,
    BehaviouralAnomalyExpert,
    IsolationForestExpert,
    TransactionVelocityExpert,
    DeviceSessionExpert,
    NetworkRiskExpert,
    RuleExpert,
)


class RiskFusionEngine:
    """
    Transparent Risk Fusion Orchestrator.
    Combines 7 specialist detection experts into an explainable aggregate consensus.
    """

    def __init__(
        self,
        supervised_expert: Optional[SupervisedFraudExpert] = None,
        behavioural_expert: Optional[BehaviouralAnomalyExpert] = None,
        isolation_expert: Optional[IsolationForestExpert] = None,
        velocity_expert: Optional[TransactionVelocityExpert] = None,
        device_expert: Optional[DeviceSessionExpert] = None,
        network_expert: Optional[NetworkRiskExpert] = None,
        rule_expert: Optional[RuleExpert] = None,
    ):
        self.supervised_expert = supervised_expert or SupervisedFraudExpert()
        self.behavioural_expert = behavioural_expert or BehaviouralAnomalyExpert()
        self.isolation_expert = isolation_expert or IsolationForestExpert()
        self.velocity_expert = velocity_expert or TransactionVelocityExpert()
        self.device_expert = device_expert or DeviceSessionExpert()
        self.network_expert = network_expert or NetworkRiskExpert()
        self.rule_expert = rule_expert or RuleExpert()

        self.experts = [
            self.supervised_expert,
            self.behavioural_expert,
            self.isolation_expert,
            self.velocity_expert,
            self.device_expert,
            self.network_expert,
            self.rule_expert,
        ]

    def set_expert_weights(self, weights: Dict[str, float]) -> None:
        """Dynamically adjusts expert weights for sensitivity tuning."""
        for expert in self.experts:
            if expert.name in weights:
                expert.weight = max(0.1, float(weights[expert.name]))

    def get_expert_configs(self) -> List[Dict[str, Any]]:
        """Returns metadata and current weights of all registered experts."""
        return [
            {
                "name": e.name,
                "category": e.category,
                "weight": e.weight,
                "description": e.__doc__.strip().split("\n")[0] if e.__doc__ else "",
            }
            for e in self.experts
        ]

    def evaluate(
        self,
        event_dict: Dict[str, Any],
        features_dict: Dict[str, float],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes all 7 specialist experts and computes transparent consensus.
        """
        expert_results: List[ExpertResult] = []
        for expert in self.experts:
            try:
                res = expert.evaluate(event_dict, features_dict, context)
                expert_results.append(res)
            except Exception as e:
                # Fault tolerance: an expert failure does not take down the entire pipeline
                expert_results.append(
                    ExpertResult(
                        expert_name=expert.name,
                        category=expert.category,
                        score=0.1,
                        confidence=0.5,
                        weight=expert.weight,
                        decision="ALLOW",
                        reasons=[f"Expert evaluation bypassed: {str(e)}"],
                    )
                )

        # 1. Weighted consensus calculation
        total_weight = sum(r.weight for r in expert_results)
        weighted_score = sum(r.weight * r.score for r in expert_results) / (total_weight or 1.0)
        weighted_confidence = sum(r.weight * r.confidence for r in expert_results) / (total_weight or 1.0)

        # 2. Consensus Voting Breakdown
        votes = {"ALLOW": 0, "REVIEW": 0, "BLOCK": 0}
        for r in expert_results:
            votes[r.decision] = votes.get(r.decision, 0) + 1

        # 3. Decision mapping
        # If any hard business rule or security expert demands BLOCK with high confidence, or weighted score >= 0.65
        rule_block = any(r.category == "BUSINESS_RULES" and r.decision == "BLOCK" for r in expert_results)
        if rule_block or weighted_score >= 0.65:
            consensus_action = "BLOCK"
        elif weighted_score >= 0.38 or votes["REVIEW"] >= 2:
            consensus_action = "REVIEW"
        else:
            consensus_action = "ALLOW"

        # 4. Top risk contributors
        sorted_by_impact = sorted(expert_results, key=lambda x: (x.score * x.weight), reverse=True)
        top_contributors = [
            {
                "expert": r.expert_name,
                "score": round(r.score, 4),
                "weighted_impact": round((r.score * r.weight) / (total_weight or 1.0), 4),
                "decision": r.decision,
                "reasons": r.reasons,
            }
            for r in sorted_by_impact
            if r.score >= 0.35
        ]

        return {
            "fused_risk_score": round(weighted_score, 4),
            "fused_confidence": round(weighted_confidence, 4),
            "consensus_action": consensus_action,
            "votes": votes,
            "total_experts": len(expert_results),
            "top_contributors": top_contributors,
            "expert_breakdown": [r.to_dict() for r in expert_results],
            "formula": "sum(weight_i * score_i) / sum(weight_i)",
            "weights_used": {r.expert_name: r.weight for r in expert_results},
        }

