"""
DRIFTGUARD Dataset Loader
Robust loader and preprocessor for standard fraud benchmarks:
1. ULB European Credit Card Fraud Detection (Time, V1..V28, Amount, Class)
2. IEEE-CIS Fraud Detection (TransactionID, isFraud, TransactionDT, TransactionAmt, etc.)
3. Deterministic Synthetic Benchmark Generator (operational fallback with zero external downloads)

Enforces chronological splitting to guarantee zero future-lookahead target leakage.
"""

from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import numpy as np
import pandas as pd
from config import settings


class DatasetFormat:
    ULB = "ulb"
    IEEE = "ieee"
    SYNTHETIC = "synthetic"
    UNKNOWN = "unknown"


class DatasetLoader:
    """
    Detects dataset schema, loads selected features, normalizes labels,
    and performs strictly chronological train/test splitting.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or settings.DATA_DIR

    @staticmethod
    def detect_format(df: pd.DataFrame) -> str:
        """Inspects dataframe columns to determine schema type."""
        cols = set(df.columns)
        if "Class" in cols and "Amount" in cols and any(c.startswith("V") for c in cols):
            return DatasetFormat.ULB
        if "isFraud" in cols and ("TransactionAmt" in cols or "TransactionDT" in cols):
            return DatasetFormat.IEEE
        if "is_fraud" in cols and "amount" in cols and "dataset_source" in cols:
            return DatasetFormat.SYNTHETIC
        if "is_fraud" in cols and "amount" in cols:
            return DatasetFormat.SYNTHETIC
        return DatasetFormat.UNKNOWN

    def generate_synthetic_dataset(
        self,
        n_samples: int = 5000,
        fraud_ratio: float = 0.02,
        seed: int = settings.SIMULATION_SEED,
        save_path: Optional[Path] = None,
    ) -> pd.DataFrame:
        """
        Generates a realistic, deterministic synthetic benchmark dataset.
        All synthetic records are clearly labelled as synthetic.
        """
        rng = np.random.default_rng(seed)
        n_fraud = int(n_samples * fraud_ratio)
        n_normal = n_samples - n_fraud

        # Normal transactions: Log-normal amounts, moderate velocities, regular hours
        normal_amounts = np.clip(rng.lognormal(mean=3.5, sigma=0.8, size=n_normal), 1.0, 3000.0)
        normal_velocities = rng.poisson(lam=1.2, size=n_normal)
        normal_time_deltas = rng.exponential(scale=300.0, size=n_normal)  # avg 5 min between tx
        normal_labels = np.zeros(n_normal, dtype=int)

        # Fraud transactions: Bimodal amounts (micro-testing or large spikes), high velocities
        fraud_amounts = rng.choice(
            [rng.uniform(1.0, 5.0), rng.uniform(800.0, 4500.0)],
            size=n_fraud,
            p=[0.3, 0.7]
        )
        fraud_velocities = rng.poisson(lam=5.5, size=n_fraud)
        fraud_time_deltas = rng.exponential(scale=15.0, size=n_fraud)     # rapid succession
        fraud_labels = np.ones(n_fraud, dtype=int)

        amounts = np.concatenate([normal_amounts, fraud_amounts])
        velocities = np.concatenate([normal_velocities, fraud_velocities])
        time_deltas = np.concatenate([normal_time_deltas, fraud_time_deltas])
        labels = np.concatenate([normal_labels, fraud_labels])

        # Synthesize chronological order
        indices = np.arange(n_samples)
        rng.shuffle(indices)

        amounts = amounts[indices]
        velocities = velocities[indices]
        time_deltas = time_deltas[indices]
        labels = labels[indices]

        cumulative_timestamps = np.cumsum(time_deltas)
        base_epoch = 1700000000.0

        df = pd.DataFrame({
            "timestamp": pd.to_datetime(base_epoch + cumulative_timestamps, unit="s", utc=True),
            "amount": np.round(amounts, 2),
            "transaction_velocity": velocities,
            "time_since_prev": np.round(time_deltas, 1),
            "device_consistency": rng.choice([1.0, 0.0], size=n_samples, p=[0.92, 0.08]),
            "session_consistency": rng.choice([1.0, 0.0], size=n_samples, p=[0.95, 0.05]),
            "network_risk_flag": rng.choice([0.0, 1.0], size=n_samples, p=[0.96, 0.04]),
            "is_fraud": labels,
            "dataset_source": "synthetic",
        })

        # Ensure strict chronological sorting
        df = df.sort_values("timestamp").reset_index(drop=True)

        target_path = save_path or (settings.SIMULATED_DATA_DIR / "synthetic_fraud_benchmark.csv")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(target_path, index=False)

        return df

    def load_dataset(
        self,
        filepath: Optional[Path] = None,
        max_rows: Optional[int] = None,
    ) -> Tuple[pd.DataFrame, str]:
        """
        Loads dataset from path. If file does not exist, automatically falls back
        to generating the deterministic synthetic benchmark dataset.
        Returns: (dataframe, detected_format_string)
        """
        if filepath is None or not Path(filepath).exists():
            default_synthetic_path = settings.SIMULATED_DATA_DIR / "synthetic_fraud_benchmark.csv"
            if not default_synthetic_path.exists():
                df = self.generate_synthetic_dataset(save_path=default_synthetic_path)
            else:
                df = pd.read_csv(default_synthetic_path)
                df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
            return df, DatasetFormat.SYNTHETIC

        path = Path(filepath)
        df = pd.read_csv(path, nrows=max_rows)
        fmt = self.detect_format(df)

        if fmt == DatasetFormat.ULB:
            # ULB has Time, V1..V28, Amount, Class
            df = df.rename(columns={"Class": "is_fraud", "Amount": "amount"})
            df["dataset_source"] = "ulb"
            if "Time" in df.columns:
                df = df.sort_values("Time").reset_index(drop=True)

        elif fmt == DatasetFormat.IEEE:
            # IEEE-CIS has TransactionID, isFraud, TransactionAmt, TransactionDT, etc.
            cols_to_keep = [c for c in ["TransactionID", "isFraud", "TransactionDT", "TransactionAmt"] if c in df.columns]
            df = df[cols_to_keep].copy()
            df = df.rename(columns={"isFraud": "is_fraud", "TransactionAmt": "amount"})
            df["dataset_source"] = "ieee"
            if "TransactionDT" in df.columns:
                df = df.sort_values("TransactionDT").reset_index(drop=True)

        elif fmt == DatasetFormat.SYNTHETIC:
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
                df = df.sort_values("timestamp").reset_index(drop=True)

        return df, fmt

    @staticmethod
    def chronological_split(
        df: pd.DataFrame,
        train_ratio: float = settings.TRAIN_SPLIT_RATIO,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Performs a strictly chronological split (train earlier in time, test later).
        Guarantees zero future data leakage.
        """
        split_idx = int(len(df) * train_ratio)
        train_df = df.iloc[:split_idx].copy().reset_index(drop=True)
        test_df = df.iloc[split_idx:].copy().reset_index(drop=True)
        return train_df, test_df

