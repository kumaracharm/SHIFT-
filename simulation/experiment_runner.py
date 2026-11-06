"""
DRIFTGUARD Experiment Runner
Executes reproducible simulation experiments, benchmarks detection pipelines,
and records run telemetry into SQLite experiment records.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from config import settings
from simulation.scenarios import ScenarioType
from ingestion.event_generator import StreamEventGenerator
from engine.event_service import EventProcessingService
from storage.repositories import ExperimentRunRepository


class ExperimentRunner:
    """Orchestrates structured benchmark experiments over synthetic streaming scenarios."""

    def __init__(self, session: Session, event_service: EventProcessingService):
        self.session = session
        self.event_service = event_service
        self.repo = ExperimentRunRepository(session)

    def run_scenario(
        self,
        scenario: ScenarioType = ScenarioType.NORMAL,
        total_events: int = 100,
        anomaly_ratio: float = 0.05,
        seed: int = settings.SIMULATION_SEED,
    ) -> Dict[str, Any]:
        """Runs a batch stream for the specified scenario and records metrics."""
        generator = StreamEventGenerator(
            key_manager=self.event_service.key_manager,
            key_id=settings.DEFAULT_KEY_ID,
            seed=seed,
        )

        run_id = f"exp_{scenario.value}_{uuid.uuid4().hex[:8]}"
        start_time = datetime.now(timezone.utc)

        rejected = 0
        flagged = 0
        decisions: Dict[str, int] = {}
        stream = generator.generate_stream(count=total_events, scenario=scenario, anomaly_ratio=anomaly_ratio)

        for event in stream:
            result = self.event_service.process_event(event)
            decisions[result.decision] = decisions.get(result.decision, 0) + 1

            if result.decision == "INTEGRITY_REJECTED":
                rejected += 1
            elif result.decision in ("HIGH_RISK", "REVIEW"):
                flagged += 1

        end_time = datetime.now(timezone.utc)
        duration_sec = (end_time - start_time).total_seconds()

        summary = {
            "run_id": run_id,
            "scenario": scenario.value,
            "total_events": total_events,
            "rejected_events": rejected,
            "flagged_events": flagged,
            "decision_breakdown": decisions,
            "duration_seconds": round(duration_sec, 3),
            "events_per_second": round(total_events / max(0.001, duration_sec), 1),
        }

        self.repo.record_run(
            run_id=run_id,
            scenario_name=scenario.value,
            start_time=start_time,
            end_time=end_time,
            total_events=total_events,
            rejected_events=rejected,
            flagged_events=flagged,
            summary=summary,
        )

        return summary

