"""
DRIFTGUARD Simulation Service
Bridges the Simulation Lab UI directly to Phase 1's ExperimentRunner and EventProcessingService.
Guarantees execution through established simulation architectures.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from storage.database import SessionLocal
from config import settings
from simulation.scenarios import ScenarioType, SCENARIO_CONFIGS
from simulation.experiment_runner import ExperimentRunner
from engine.event_service import EventProcessingService
from models.prediction_service import PredictionService
from models.model_registry import ModelRegistry
from security.key_manager import KeyManager


class SimulationService:
    """Manages real simulation executions, scenarios, and experiment runs."""

    def __init__(self):
        self.key_manager = KeyManager()
        self.key_manager.load_or_create_default_key(settings.DEFAULT_KEY_ID)

    def execute_scenario(
        self,
        scenario: ScenarioType,
        event_count: int = 50,
        anomaly_ratio: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Executes a deterministic simulation scenario through the complete Phase 1 pipeline.
        Records run metadata into SQLite and returns detailed execution metrics.
        """
        session: Session = SessionLocal()
        try:
            # Ensure model is available
            registry = ModelRegistry(session)
            clf = registry.load_active_fraud_model()
            pred_service = PredictionService(fraud_classifier=clf)

            event_service = EventProcessingService(
                session=session,
                key_manager=self.key_manager,
                prediction_service=pred_service,
                enforce_freshness=True,
            )

            runner = ExperimentRunner(session=session, event_service=event_service)
            summary = runner.run_scenario(
                scenario=scenario,
                total_events=event_count,
                anomaly_ratio=anomaly_ratio,
            )
            return summary
        finally:
            session.close()

    @staticmethod
    def get_available_scenarios() -> Dict[ScenarioType, Dict[str, Any]]:
        """Returns metadata and configurations for all supported simulation scenarios."""
        return SCENARIO_CONFIGS

