# SHIFT — Known Limitations

> **Principle**: This document is an honest, unfiltered assessment. We do not hide weaknesses.

---

## 1. WebSocket Background Thread (Windows Event Loop)

**Severity**: Low — demo impact only  
**Component**: `backend/routers/simulation.py` → `_background_worker()`

When simulation is set to auto-run continuously, the background thread calls `asyncio.run()` to broadcast to WebSocket clients. On Windows, this creates a new event loop per call, which can conflict with uvicorn's running loop, causing broadcast failures.

**Workaround in place**: The `step_simulation` endpoint and `inject` endpoint broadcast correctly because they run in the FastAPI async context. Live demonstrations should use "Step" and "Inject" buttons rather than the auto-continuous mode.

**What this does NOT affect**: All REST API endpoints, database persistence, ML scoring, drift detection, and experiment results are unaffected. Only live WebSocket push during continuous streaming is impacted.

---

## 2. PSI Bin Visualisation Uses Illustrative Distributions

**Severity**: Very low — visual only  
**Component**: `backend/routers/drift.py` → `get_feature_drift_breakdown()`

The PSI *score* is computed from real streaming data. However, the 5-bin distribution comparison displayed in the Drift Analytics charts uses a heuristic: the bin proportions shown are illustrative patterns (e.g., `[0.45, 0.25, 0.15, 0.10, 0.05]`) rather than actual quantile histograms computed from the raw feature values.

**What is real**: The PSI score itself, computed by `FeatureDistributionMonitor.evaluate_all()`, reflects genuine statistical divergence between the baseline reference window and the current rolling window.

---

## 3. Supervised Model Operates on 8 Streaming Features, Not 96 IEEE-CIS Features

**Severity**: Medium — affects fraud probability calibration  
**Component**: `models/fraud_classifier.py`, `models/experts/specialists.py`

The IEEE-CIS Random Forest was trained on 96-column tabular features. At inference, it receives only 8 streaming features (zero-padded to 96). This means the RF's fraud probability scores are not well-calibrated for the synthetic UPI stream — they will tend to output low scores.

**Why this is architecturally correct**: The RF score is one of 7 expert signals. The Risk Fusion Engine combines it with Velocity, Device, Network, Rule, and anomaly experts that *do* operate on the 8 streaming features. The final fused risk score is well-calibrated.

**Impact on the ROC-AUC claim**: The 0.8954 ROC-AUC is a valid holdout metric on the **IEEE-CIS dataset** only. We do not claim this AUC on synthetic UPI data.

---

## 4. No Real UPI / NPCI Connectivity

**What it is**: By design — this is not a limitation.

The system explicitly does **not** claim any connection to the NPCI network, any live UPI rail, any bank's API, or any real-time payment stream. All UPI traffic is internally generated synthetic simulation data, clearly marked `event_source = SYNTHETIC_UPI_SIMULATION`.

This is architecturally correct for a research/demonstration system.

---

## 5. ADWIN Drift Detection Requires Sufficient Observations

**Severity**: Low  
**Component**: `drift/adwin_monitor.py`

ADWIN requires a minimum number of observations in its sliding window before it can fire reliably. With fewer than ~20 events, the window is too small to compute meaningful statistical splits. During the first few seconds of a fresh simulation, ADWIN will not fire even if data is anomalous.

**Mitigation**: The Moving Target Experiment is designed with Phase 1 (80 baseline events) specifically to build up ADWIN's reference window before phases 2 and 3 introduce anomalies.

---

## 6. No Auto-Retraining on Unlabelled Suspicious Data

**What it is**: An intentional architectural principle, not a limitation.

SHIFT never automatically retrains or adapts its model weights based on unlabelled suspicious events. Doing so would cause model poisoning risk. The system escalates *detection sensitivity* (policy thresholds) in response to drift detection, but model updates require verified ground-truth labels via the `observe_ground_truth()` API.

---

## 7. SQLite Concurrency

**Severity**: Low — demo scale only  
**Component**: `storage/database.py`

SQLite has file-level write locking. Under high concurrency (>10 simultaneous requests that write), occasional lock contention may cause brief delays. At hackathon demonstration scale (1–5 concurrent users, 1–5 tx/s), this is not observable.

For production deployment, replace SQLite with PostgreSQL by swapping the `DATABASE_URL` in `config.py`.

---

## 8. Experiment Reproducibility Depends on StreamController State

**Severity**: Low  
**Component**: `simulation/moving_target_experiment.py`

The `StreamController` maintains in-memory user/device history. If two experiments are run sequentially in the same process, the second experiment's velocity and device consistency features will be influenced by the first experiment's state. Use separate process invocations (e.g., `python scripts/run_moving_target_experiment.py`) for fully independent reproducible runs.

---

## Summary

None of the above limitations affect the core SHIFT innovation demonstration:

> **SHIFT detects moving-target fraud behaviour change using unlabelled streaming ADWIN signals, before ground-truth labels arrive.**

This is fully implemented, experimentally verified, and reproducible.

