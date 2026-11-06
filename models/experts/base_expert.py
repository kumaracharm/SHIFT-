"""
DRIFTGUARD 2.0 Base Specialist Expert Interface
Defines the contract for the 7 specialist detection experts.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class ExpertResult:
    expert_name: str
    category: str
    score: float  # [0.0, 1.0]
    confidence: float  # [0.0, 1.0]
    weight: float
    decision: str  # ALLOW, REVIEW, BLOCK
    reasons: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "expert_name": self.expert_name,
            "category": self.category,
            "score": round(self.score, 4),
            "confidence": round(self.confidence, 4),
            "weight": round(self.weight, 2),
            "decision": self.decision,
            "reasons": self.reasons,
            "metadata": self.metadata,
        }


class BaseExpert(ABC):
    """Abstract base class for all detection experts."""

    def __init__(self, name: str, category: str, default_weight: float = 1.0):
        self.name = name
        self.category = category
        self.weight = default_weight

    @abstractmethod
    def evaluate(
        self,
        event_dict: Dict[str, Any],
        features_dict: Dict[str, float],
        context: Optional[Dict[str, Any]] = None,
    ) -> ExpertResult:
        """Evaluates transaction attributes and outputs an ExpertResult."""
        pass

