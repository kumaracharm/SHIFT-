# IEEE-CIS Real Fraud Detection Dataset Training & Profiling

This document outlines the end-to-end pipeline for dataset profiling, memory-conscious tabular preprocessing, model training, and holdout evaluation in DRIFTGUARD.

---

## 1. Dataset Characteristics

- **Competition:** IEEE-CIS Fraud Detection
- **Primary Source:** Vesta Corporation & IEEE Computational Intelligence Society
- **Tables:**
  - `train_transaction.csv`: 590,540 rows × 394 columns (~613 MB uncompressed)
  - `train_identity.csv`: 144,233 rows × 41 columns (~26.5 MB uncompressed)
- **Target:** `isFraud` (1 = Fraud, 0 = Legitimate)
- **Severe Class Imbalance:** ~3.5% Fraud, ~96.5% Legitimate (~28:1 ratio)

---

## 2. Memory-Conscious Tabular Engineering

To ensure stability on local workstations with 4 GB GPU / 16 GB RAM:

1. **Selective Column Loading:**
   - Rather than loading 435 raw columns, DRIFTGUARD selects a high-signal subset of ~75 numeric and categorical features.
   - Appropriate dtypes: `float32` for continuous metrics, `int32` for identifiers, and frequency-limited category mapping.
2. **Relational Join:**
   - Left join on `TransactionID`. Transactions without identity records are retained with identity fields designated as unavailable (no fabricated metadata).
3. **Chronological Splitting:**
   - Sorted by `TransactionDT` (relative seconds offset spanning ~182 days).
   - **70% Training:** 0 to 70th percentile of `TransactionDT`.
   - **15% Validation:** 70th to 85th percentile (used strictly for threshold tuning).
   - **15% Untouched Holdout:** 85th to 100th percentile (final zero-leakage evaluation).
4. **Leakage Prevention:**
   - All median imputers and categorical vocabularies are fit **exclusively** on the 70% training split and applied downstream.

---

## 3. Profiling Execution

Generate the complete exploratory data analysis report and JSON profile:

```powershell
python scripts/profile_ieee_cis.py
```

Outputs:
- `data/processed/dataset_profile.json`
- `data/processed/ieee_cis_eda_report.md`

---

## 4. Model Training & Evaluation Execution

Train the supervised Random Forest model, optimize decision thresholds, and register the artifact:

```powershell
python scripts/train_ieee_cis.py
```

Outputs:
- Model Artifact: `saved_models/rf_ieee_cis_v1.joblib`
- Evaluation JSON: `data/processed/model_evaluation.json`
- Comparison Report: `data/processed/model_comparison.md`
- Active Registration in SQLite: Table `model_versions`

