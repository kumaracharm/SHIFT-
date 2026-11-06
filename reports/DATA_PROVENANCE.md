# SHIFT — Data Provenance & Environment Separation Report

> **System**: SHIFT — Streaming Hybrid Intelligence for Fraud Tracking  
> **Topic**: Strict Separation of Historical Benchmark Data and Synthetic Simulation Streams  
> **Date**: 2026-11-06  

---

## 1. Provenance Statement & Integrity Guarantee

To ensure scientific rigor, avoid data leakage, and maintain realistic evaluation standards, SHIFT maintains **strict, irrevocable separation** between historical benchmark data and streaming simulation data:

1. **Historical Tabular Benchmark**: Real-world IEEE-CIS Fraud Detection dataset.
2. **Streaming Transaction Lab**: Deterministic Synthetic UPI (Unified Payments Interface) stream.

**Invariant Rule**: These two data environments are **never mixed, joined, or merged** into a single evaluation dataset. Every transaction record carries a permanent provenance marker `event_source`.

---

## 2. Environment A: Historical IEEE-CIS Fraud Benchmark

### 2.1. Dataset Metadata
- **Source**: Vesta Corporation / IEEE Computational Intelligence Society (Kaggle Competition: `ieee-fraud-detection`).
- **Storage Location**: `data/raw/ieee_cis/`
- **Core Files**:
  - `train_transaction.csv` (651 MB, 590,540 rows, 394 features)
  - `train_identity.csv` (25 MB, 144,233 rows, 41 features)
- **Provenance Tag**: `event_source = IEEE_CIS_HISTORICAL`

### 2.2. Preprocessing & Chronological Splitting
Real-world fraud detection violates IID assumptions because fraud patterns evolve over time. Random k-fold cross-validation results in severe data leakage.

SHIFT applies **strict chronological train/validation/holdout splitting** using `TransactionDT`:
- **Training Set**: Earliest 70,000 transactions (50% chronological partition).
- **Validation Set**: Subsequent 15,000 transactions (tuning decision thresholds).
- **Test Holdout Set**: Final 15,000 transactions (unseen future time window).

### 2.3. Model Artifact
- **Saved Model**: `saved_models/rf_ieee_cis_v1.joblib`
- **Holdout Performance**:
  - **ROC-AUC**: `0.8954`
  - **PR-AUC**: `0.4575`
  - **Optimal Precision**: `0.5123`
  - **Optimal Recall**: `0.5443`
  - **Optimal F1-Score**: `0.5278`
  - **Evaluation Artifact**: `data/processed/model_evaluation.json`

---

## 3. Environment B: Synthetic UPI Streaming Simulation

### 3.1. Purpose & Scope
The synthetic UPI stream powers real-time simulation, WebSocket streaming, scenario injection, and the 6-phase moving target experiment.

- **Storage Location**: `data/synthetic_upi/`
- **Provenance Tag**: `event_source = SYNTHETIC_UPI_SIMULATION`
- **Strict Constraint**: SHIFT makes **zero claim of live connectivity** to the National Payments Corporation of India (NPCI) or any live banking rail. All UPI payment references, VPAs, and devices are deterministically synthesized.

### 3.2. Synthetic Feature Generation
The synthetic engine generates realistic Indian digital payment semantics:
- **Entities**: 50 persistent simulated users, 20 popular Indian merchants, realistic VPAs (`user@okhdfcbank`, `merchant@icici`).
- **Amounts**: Realistic log-normal distribution centered around ₹850.00 for peer-to-peer/merchant transactions.
- **Geographic & Network Context**: Realistic Indian tier-1/tier-2 cities (Bengaluru, Mumbai, Delhi, Hyderabad, Pune) mapped to authentic Indian Autonomous System Numbers (ASNs: Jio AS55836, Airtel AS45609, ACT AS24309).

### 3.3. 19 Deterministic Scenarios
Covering benign traffic, statistical shifts, and active cyber attacks:

| Scenario Group | Scenario Types |
|----------------|----------------|
| **Benign Traffic** | `UPI_NORMAL`, `NORMAL`, `REAL_DATA_REPLAY` |
| **Statistical Shift** | `UPI_AMOUNT_SPIKE`, `AMOUNT_SPIKE`, `LOW_AND_SLOW` |
| **Velocity & Pacing** | `UPI_VELOCITY_BURST`, `VELOCITY_BURST` |
| **Identity & Payee** | `UPI_NEW_PAYEE`, `UPI_DEVICE_CHANGE`, `DEVICE_SWITCH` |
| **Network & Location** | `UPI_LOCATION_JUMP`, `NETWORK_HOP` |
| **Cyber & Cryptographic Attacks** | `UPI_TAMPERED`, `TAMPERED_SIGNATURE`, `UPI_REPLAY_ATTACK`, `REPLAY_ATTACK` |
| **Coordinated Crime** | `UPI_MULE_RING`, `FRAUD_PATTERN_SHIFT` |

---

## 4. Architectural Data Guardrails

1. **Database Schema Enforcement**: `PredictionRecord` in SQLite stores `dataset_source` and payload metadata to ensure historical analysis never pollutes simulation metrics.
2. **Model Training Isolation**: The supervised Random Forest model is trained exclusively on IEEE-CIS data. It is never trained or updated using synthetic UPI events.
3. **Transparent Reporting**: Every metrics chart and audit card in the Next.js UI explicitly displays data source tags so analysts and evaluators can immediately identify the underlying environment.

