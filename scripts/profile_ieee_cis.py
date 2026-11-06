"""
DRIFTGUARD IEEE-CIS Dataset Profiler and EDA Reporter
Inspects raw transaction and identity CSVs, analyzes data types, missing rates,
join completeness, target distribution, and generates:
- data/processed/dataset_profile.json
- data/processed/ieee_cis_eda_report.md
"""

import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import settings

RAW_DIR = settings.RAW_DATA_DIR / "ieee_cis"
PROCESSED_DIR = settings.PROCESSED_DATA_DIR
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

TX_FILE = RAW_DIR / "train_transaction.csv"
ID_FILE = RAW_DIR / "train_identity.csv"


def profile_dataset() -> dict:
    print("=" * 70)
    print("DRIFTGUARD: IEEE-CIS Dataset Profiling & Validation")
    print("=" * 70)

    if not TX_FILE.exists():
        print(f"[ERROR] Transaction file not found at: {TX_FILE}")
        sys.exit(1)

    # 1. File sizes
    tx_size_mb = TX_FILE.stat().st_size / (1024 * 1024)
    id_size_mb = ID_FILE.stat().st_size / (1024 * 1024) if ID_FILE.exists() else 0.0

    print(f"[1/6] Inspecting file sizes...")
    print(f"  train_transaction.csv : {tx_size_mb:.2f} MB")
    print(f"  train_identity.csv    : {id_size_mb:.2f} MB")

    # 2. Memory-efficient load of transaction table (load essential header and metadata)
    print(f"[2/6] Loading train_transaction.csv schema and row counts...")
    # Count rows fast
    with open(TX_FILE, "r", encoding="utf-8") as f:
        total_tx_rows = sum(1 for _ in f) - 1

    # Load sample to inspect headers & dtypes
    df_tx_sample = pd.read_csv(TX_FILE, nrows=5000)
    tx_cols = list(df_tx_sample.columns)

    # 3. Target Distribution & Duplicates
    print(f"[3/6] Inspecting target distribution and TransactionID uniqueness...")
    df_tx_target = pd.read_csv(TX_FILE, usecols=["TransactionID", "isFraud", "TransactionDT", "TransactionAmt"])
    is_tx_unique = df_tx_target["TransactionID"].is_unique
    fraud_counts = df_tx_target["isFraud"].value_counts().to_dict()
    n_fraud = int(fraud_counts.get(1, 0))
    n_legit = int(fraud_counts.get(0, 0))
    total_tx = len(df_tx_target)
    fraud_rate = n_fraud / max(1, total_tx)

    print(f"  Total Transactions: {total_tx:,}")
    print(f"  Legitimate (0)    : {n_legit:,} ({n_legit/total_tx:.2%})")
    print(f"  Fraudulent (1)    : {n_fraud:,} ({fraud_rate:.2%})")
    print(f"  TransactionID Unique: {is_tx_unique}")

    # 4. Identity Join Verification
    print(f"[4/6] Verifying identity table join relationship...")
    if ID_FILE.exists():
        with open(ID_FILE, "r", encoding="utf-8") as f:
            total_id_rows = sum(1 for _ in f) - 1
        df_id_sample = pd.read_csv(ID_FILE, nrows=5000)
        id_cols = list(df_id_sample.columns)

        df_id_ids = pd.read_csv(ID_FILE, usecols=["TransactionID"])
        is_id_unique = df_id_ids["TransactionID"].is_unique
        id_set = set(df_id_ids["TransactionID"])
        tx_set = set(df_tx_target["TransactionID"])
        joined_count = len(tx_set.intersection(id_set))
        id_match_rate = joined_count / max(1, total_tx)
    else:
        total_id_rows = 0
        id_cols = []
        is_id_unique = True
        joined_count = 0
        id_match_rate = 0.0

    print(f"  Total Identity Rows: {total_id_rows:,}")
    print(f"  Transactions with Identity: {joined_count:,} ({id_match_rate:.2%})")

    # 5. Missing value analysis on sample
    print(f"[5/6] Analyzing missing value patterns...")
    missing_rates = (df_tx_sample.isnull().mean() * 100).sort_values(ascending=False)
    high_missing_cols = missing_rates[missing_rates > 50].count()
    low_missing_cols = missing_rates[missing_rates <= 10].count()

    # 6. Build Profile Dictionary
    profile = {
        "dataset_name": "IEEE-CIS Fraud Detection",
        "competition": "ieee-fraud-detection",
        "files": {
            "train_transaction.csv": {
                "size_mb": round(tx_size_mb, 2),
                "rows": total_tx,
                "columns": len(tx_cols),
            },
            "train_identity.csv": {
                "size_mb": round(id_size_mb, 2),
                "rows": total_id_rows,
                "columns": len(id_cols),
            },
        },
        "target_distribution": {
            "total_transactions": total_tx,
            "legitimate_count": n_legit,
            "fraud_count": n_fraud,
            "fraud_percentage": round(fraud_rate * 100, 3),
        },
        "identity_join": {
            "transactions_with_identity": joined_count,
            "identity_coverage_pct": round(id_match_rate * 100, 2),
            "join_key": "TransactionID",
            "relationship": "1:0..1 (optional identity extension)",
        },
        "data_hygiene": {
            "duplicate_transaction_ids": total_tx - len(set(df_tx_target["TransactionID"])),
            "high_missing_feature_count": int(high_missing_cols),
            "low_missing_feature_count": int(low_missing_cols),
            "temporal_feature": "TransactionDT (seconds offset)",
            "amount_feature": "TransactionAmt",
        },
    }

    # Save dataset_profile.json
    profile_path = PROCESSED_DIR / "dataset_profile.json"
    profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    print(f"\n[OK] Saved dataset profile to: {profile_path}")

    # Generate Markdown EDA Report
    report_md = f"""# IEEE-CIS Fraud Detection — Exploratory Data Analysis Report
**Generated for DRIFTGUARD Real-Data Model Engineering**

## 1. Dataset Provenance & File Inventory
- **Source:** Kaggle IEEE-CIS Fraud Detection (`https://www.kaggle.com/competitions/ieee-fraud-detection`)
- **Organized by:** IEEE Computational Intelligence Society (IEEE-CIS) & Vesta Corporation
- **License:** Subject to Competition Rules (Strictly for Research & Evaluation)

| File Name | File Size | Row Count | Column Count |
|:---|:---:|:---:|:---:|
| `train_transaction.csv` | {tx_size_mb:.2f} MB | {total_tx:,} | {len(tx_cols)} |
| `train_identity.csv` | {id_size_mb:.2f} MB | {total_id_rows:,} | {len(id_cols)} |

## 2. Target Distribution & Class Imbalance
The primary prediction target is `isFraud`:
- **Legitimate Transactions (Class 0):** {n_legit:,} ({n_legit/total_tx:.2%})
- **Fraudulent Transactions (Class 1):** {n_fraud:,} ({fraud_rate:.2%})
- **Severe Imbalance Ratio:** ~28 : 1

> **Implication for Model Architecture:** Standard accuracy is completely misleading for this distribution (a naive 0-predictor achieves ~96.5% accuracy). DRIFTGUARD enforces **Precision, Recall, F1-Score, and PR-AUC** as primary evaluation benchmarks, alongside balanced class weighting.

## 3. Relational Structure & Identity Coverage
- **Join Key:** `TransactionID` (unique identifier in both tables).
- **Identity Presence:** {joined_count:,} out of {total_tx:,} transactions ({id_match_rate:.2%}) have associated identity metadata.
- **Architectural Policy:** A Left Join from `train_transaction` onto `train_identity` is maintained. Transactions without identity metadata are never dropped; missing identity fields are explicitly designated as `unavailable` to prevent hallucinating context.

## 4. Temporal Integrity & Lookahead Prevention
- **`TransactionDT`:** Continuous relative time delta (in seconds from an arbitrary epoch, covering ~182 days).
- **Evaluation Strategy:** Strictly chronological train/validation/holdout split based on `TransactionDT`.
  - Earliest 70%: Training Set
  - Middle 15%: Validation Set (Threshold Tuning)
  - Final 15%: Untouched Holdout Test Set (Zero Lookahead Target Leakage)

## 5. Feature Engineering Alignment with DRIFTGUARD
The following features are synthesized and aligned with the DRIFTGUARD pipeline:
- `TransactionAmt` -> Monetary amount, log-transform, and rolling device/card z-scores.
- `TransactionDT` -> Temporal delta, time since previous transaction, and velocity bursts.
- `DeviceInfo`, `id_30` (OS), `id_31` (Browser) -> Device consistency scoring.
- `P_emaildomain`, `R_emaildomain`, `addr1`, `addr2` -> Network/routing context.
- `card1`..`card6` -> Card/account entity tracking.
"""

    report_path = PROCESSED_DIR / "ieee_cis_eda_report.md"
    report_path.write_text(report_md, encoding="utf-8")
    print(f"[OK] Saved EDA report to: {report_path}")

    return profile


if __name__ == "__main__":
    profile_dataset()

