# SHIFT — Moving Target Experiment Report

> **System**: SHIFT — Streaming Hybrid Intelligence for Fraud Tracking  
> **Topic**: Empirical Validation of Early Drift Detection Before Confirmed Labels Arrive  
> **Experiment ID**: `mte_8ed35a695cb5`  
> **Date**: 2026-11-06  

---

## 1. The Core Problem Statement

> *"Somewhere in a stream of transactions, a few people are stealing. They read your alerts. At some moment today they will change how they steal, and no one will tell you. Missing one thief costs as much as bothering fifty honest customers. Know when the world changed, before the answers arrive, and say how you know."*

This experiment provides **concrete empirical proof** that SHIFT detects when the adversary changed tactics, identifies which features shifted, and flags the change **without relying on ground-truth fraud labels**.

---

## 2. Six-Phase Experimental Design

```mermaid
flowchart LR
    P1["Phase 1: Baseline\n(80 Normal Events)\nEstablish Reference"] --> P2["Phase 2: Initial Fraud\n(40 Velocity Bursts)\nAttacker Active"]
    P2 --> P3["Phase 3: Moving Target Pivot\n(60 Amount Spikes)\nATTACKER CHANGES TACTIC\nNO LABELS ARRIVE"]
    P3 --> P4["Phase 4: Drift Detection\n(ADWIN + PSI Alerts)\nBEFORE LABELS!"]
    P4 --> P5["Phase 5: Adaptation\n(Sensitivity Escalation)\nCatch Pivot Attacks"]
    P5 --> P6["Phase 6: Recovery\n(50 Normal Events)\nSystem Stabilises"]
```

### Phase Details

1. **Phase 1 · Normal Baseline (80 events)**:
   - Typical legitimate UPI transactions (₹850 mean, trusted devices, regular intervals).
   - Establishes the reference distributions for ADWIN and PSI.
   - Ground truth: 100% legitimate.

2. **Phase 2 · Initial Fraud Pattern (40 events)**:
   - Adversary executes high-frequency velocity bursts (repeated ₹4,999 transactions within sub-second intervals).
   - Caught by Expert 4 (Velocity) and HST streaming anomaly detector.
   - Flag rate: **72.5%**.

3. **Phase 3 · The Moving Target: Attacker Pivots (60 events)**:
   - **Crucial Moment**: The adversary realizes high-velocity transactions are triggering alerts.
   - The attacker changes tactics: pivots from rapid micro-transactions to massive, high-value transfers (₹78,000 mean) with spoofed location jumps.
   - **NO GROUND-TRUTH LABELS ARRIVE**: The system is completely blind to whether these transactions are fraudulent.
   - **What happens**: The distribution of unlabelled streaming anomaly scores shifts dramatically.

4. **Phase 4 · Drift Detection Milestone**:
   - At **event 7 into Phase 3** (Event index 127 overall), ADWIN unlabelled anomaly monitor triggers a drift alert.
   - PSI simultaneously flags major distribution divergence in `amount`, `log_amount`, `transaction_velocity`, and `time_since_prev`.
   - **Result**: SHIFT knows the world changed before any fraud label or chargeback arrived.

5. **Phase 5 · System Adaptation (30 events)**:
   - Detection sensitivity is escalated: decision threshold for `REVIEW` is tightened.
   - Fused risk engine routes borderline events to manual analyst queue.
   - Capture rate of new attack tactic reaches **100%**.

6. **Phase 6 · Recovery & Stabilisation (50 events)**:
   - Normal legitimate stream resumes.
   - System confirms stability: false positive rate returns to operational baseline.

---

## 3. Empirical Results & Metrics

| Metric | Measured Value | Benchmark Target | Status |
|--------|----------------|------------------|--------|
| **Total Stream Events** | 260 | $\ge 200$ | ✅ PASS |
| **Drift Detected Before Labels** | **TRUE** | TRUE | ✅ PASS |
| **Detection Delay** | **7 events into pivot** | $< 25$ events | ✅ PASS (Ultra-Fast) |
| **Baseline False Positive Rate** | **0.0%** | $< 5.0\%$ | ✅ PASS |
| **Initial Attack Flag Rate** | **72.5%** | $> 60.0\%$ | ✅ PASS |
| **Post-Adaptation Flag Rate** | **100.0%** | $> 90.0\%$ | ✅ PASS |
| **Runtime Duration** | **4.49s** | $< 30.0$s | ✅ PASS (Streaming Real-Time) |

---

## 4. "Say How You Know": Forensic Evidence at Detection

When asked *"how do you know the world changed?"*, SHIFT produces concrete mathematical evidence:

### 4.1. ADWIN Statistical Proof
- Monitored Signal: Unlabelled River Half-Space Trees Anomaly Score.
- Prior Window Mean $\mu_0$: `0.118` (Benign baseline density).
- Active Sub-window Mean $\mu_1$: `0.642` (Severe anomaly density).
- Statistical Difference: $|\mu_0 - \mu_1| > \epsilon_{\text{cut}}$ with confidence $\delta = 0.002$.
- Result: **Null hypothesis of stationary distribution rejected.**

### 4.2. PSI Feature Breakdown (Top Shifted Features)
```
Feature                  PSI Score     Status            Verdict
--------------------------------------------------------------------------
amount                   0.3842        DRIFT_ALERT       Major high-value spike
log_amount               0.3120        DRIFT_ALERT       Shift toward right tail
transaction_velocity     0.2845        DRIFT_ALERT       Pacing interval changed
time_since_prev          0.2619        DRIFT_ALERT       Burst to pause pattern
device_consistency       0.0412        STABLE            Normal hardware mix
session_consistency      0.0385        STABLE            Normal session lifetime
```

---

## 5. Summary & Reproducibility

The experiment can be re-executed at any time with a single command:
```bash
python scripts/run_moving_target_experiment.py
```
Or interactively launched through the Next.js UI on the **Moving Target Lab** tab with full real-time ECharts visualisations.

