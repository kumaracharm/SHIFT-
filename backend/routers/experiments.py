"""
SHIFT Moving Target Experiment Router
Provides REST API endpoints for running, listing and inspecting moving-target experiments.
"""

import os
import json
import glob
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

router = APIRouter(prefix="/api/v1/experiments", tags=["Experiments"])

EXPERIMENTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "reports", "experiments"
)


def _load_all_experiments() -> List[Dict[str, Any]]:
    """Load all saved experiment JSON files, ordered by modification time (newest first)."""
    os.makedirs(EXPERIMENTS_DIR, exist_ok=True)
    files = sorted(
        glob.glob(os.path.join(EXPERIMENTS_DIR, "*.json")),
        key=os.path.getmtime,
        reverse=True,
    )
    results = []
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                results.append(json.load(fh))
        except Exception:
            pass
    return results


@router.get("/")
def list_experiments() -> Dict[str, Any]:
    """Lists all saved moving-target experiment results."""
    experiments = _load_all_experiments()
    summaries = []
    for exp in experiments:
        summaries.append({
            "experiment_id": exp.get("experiment_id"),
            "experiment_name": exp.get("experiment_name"),
            "start_time": exp.get("start_time"),
            "total_events": exp.get("total_events"),
            "drift_detected_before_labels": exp.get("drift_detected_before_labels"),
            "drift_detection_delay_events": exp.get("drift_detection_delay_events"),
            "duration_seconds": exp.get("duration_seconds"),
        })
    return {"status": "success", "total": len(summaries), "experiments": summaries}


@router.get("/latest/result")
def get_latest_experiment() -> Dict[str, Any]:
    """Returns the most recent moving-target experiment result."""
    experiments = _load_all_experiments()
    if not experiments:
        return {"status": "no_data", "experiment": None}
    return {"status": "success", "experiment": experiments[0]}


@router.get("/{experiment_id}")
def get_experiment(experiment_id: str) -> Dict[str, Any]:
    """Retrieves full details of a specific experiment by ID."""
    experiments = _load_all_experiments()
    for exp in experiments:
        if exp.get("experiment_id") == experiment_id:
            return {"status": "success", "experiment": exp}
    raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found")


@router.post("/run")
def run_moving_target_experiment(
    seed: int = 42, name: str = "Moving Target Attack Simulation"
) -> Dict[str, Any]:
    """
    Executes a full 6-phase moving-target experiment and returns the result.
    This may take 10-30 seconds depending on the system.
    """
    try:
        from simulation.moving_target_experiment import MovingTargetExperiment
        exp = MovingTargetExperiment(seed=seed, experiment_name=name)
        result = exp.run()

        # Convert dataclasses to dict for JSON response
        from dataclasses import asdict
        result_dict = asdict(result)
        return {"status": "success", "experiment": result_dict}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Experiment failed: {str(e)}")
