"""
SHIFT Moving Target Experiment Script
Run this to execute and save a complete 6-phase moving-target experiment.

Usage:
    python scripts/run_moving_target_experiment.py
"""

import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.moving_target_experiment import MovingTargetExperiment


def main():
    print("=" * 65)
    print("SHIFT — Streaming Hybrid Intelligence for Fraud Tracking")
    print("Moving Target Experiment Runner")
    print("=" * 65)
    print()

    exp = MovingTargetExperiment(seed=42, experiment_name="Moving Target Attack Simulation v1")
    
    print("Running 6-phase experiment...")
    print("  Phase 1: Normal baseline (80 events) -> Reference distributions")
    print("  Phase 2: Velocity burst fraud (40 events) -> Initial attack pattern")
    print("  Phase 3: Attacker pivots (60 events) [BLIND / UNLABELLED]")
    print("  Phase 4: Drift detection via ADWIN + PSI")
    print("  Phase 5: Adaptation + sensitivity escalation (30 events)")
    print("  Phase 6: Recovery & stabilisation (50 events)")
    print()

    result = exp.run()

    print(f"Experiment ID: {result.experiment_id}")
    print(f"Total events:  {result.total_events}")
    print(f"Duration:      {result.duration_seconds:.2f}s")
    print()
    print("Phase Summary:")
    for phase in result.phases:
        print(f"  [{phase.phase.upper():20s}] {phase.total_events:3d} events | "
              f"flag_rate={phase.flag_rate:.1%} | "
              f"adwin_drifts={phase.adwin_drifts_detected} | "
              f"psi_alerts={phase.psi_violations}")
    print()
    
    if result.drift_detected_before_labels:
        print(f"  [PASS] DRIFT DETECTED BEFORE LABELS")
        print(f"         Detection delay: {result.drift_detection_delay_events} events into moving-target phase")
        print(f"         PSI evidence features: {list(result.psi_evidence.keys())}")
    else:
        print("  [WARN] No ADWIN drift triggered")
    
    print()
    print(f"Innovation Summary: {result.innovation_summary}")
    print()
    print(f"Artifact Saved: reports/experiments/{result.experiment_id}.json")


if __name__ == "__main__":
    main()

