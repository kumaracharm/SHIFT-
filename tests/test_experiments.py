"""
SHIFT Moving Target Experiment Test Suite
Verifies the 6-phase moving target experiment execution,
unlabelled drift detection before labels, and the experiment API router.
"""

import pytest
from simulation.moving_target_experiment import MovingTargetExperiment, ExperimentPhase
from backend.routers.experiments import list_experiments, get_latest_experiment


def test_moving_target_experiment_execution():
    """Verify that the 6-phase moving target experiment runs and completes."""
    exp = MovingTargetExperiment(seed=123, experiment_name="Test Moving Target Run")
    result = exp.run()

    assert result.experiment_id.startswith("mte_")
    assert result.total_events > 0
    assert len(result.phases) >= 6
    assert result.drift_detected_before_labels is True
    assert result.drift_detection_delay_events is not None
    assert result.drift_detection_delay_events > 0

    # Verify key phases exist
    phase_names = [p.phase for p in result.phases]
    assert ExperimentPhase.BASELINE.value in phase_names
    assert ExperimentPhase.INITIAL_FRAUD.value in phase_names
    assert ExperimentPhase.MOVING_TARGET.value in phase_names
    assert ExperimentPhase.DRIFT_DETECTION.value in phase_names
    assert ExperimentPhase.ADAPTATION.value in phase_names
    assert ExperimentPhase.RECOVERY.value in phase_names


def test_experiments_api_endpoints():
    """Verify that experiments API functions return valid dictionary payloads."""
    res_list = list_experiments()
    assert res_list["status"] == "success"
    assert "experiments" in res_list
    assert len(res_list["experiments"]) >= 1

    res_latest = get_latest_experiment()
    assert res_latest["status"] == "success"
    assert res_latest["experiment"] is not None
    assert "experiment_id" in res_latest["experiment"]
    assert "phases" in res_latest["experiment"]

