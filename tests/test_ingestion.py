"""
DRIFTGUARD Ingestion and Dataset Loader Tests
Verifies dataset loading, format detection, chronological train/test splitting, and streaming event generators.
"""

from pathlib import Path
import pandas as pd
import pytest
from ingestion.dataset_loader import DatasetLoader, DatasetFormat
from ingestion.event_generator import StreamEventGenerator
from simulation.scenarios import ScenarioType


def test_synthetic_dataset_generation(tmp_path):
    loader = DatasetLoader(data_dir=tmp_path)
    csv_path = tmp_path / "test_synth.csv"
    df = loader.generate_synthetic_dataset(n_samples=200, fraud_ratio=0.05, save_path=csv_path)

    assert len(df) == 200
    assert "amount" in df.columns
    assert "is_fraud" in df.columns
    assert "dataset_source" in df.columns
    assert (df["dataset_source"] == "synthetic").all()
    assert (df["amount"] > 0).all()
    assert df["is_fraud"].sum() > 0  # Contains labelled frauds


def test_format_detection_synthetic():
    df = pd.DataFrame({
        "timestamp": ["2026-01-01T00:00:00Z"],
        "amount": [100.0],
        "is_fraud": [0],
        "dataset_source": ["synthetic"],
    })
    fmt = DatasetLoader.detect_format(df)
    assert fmt == DatasetFormat.SYNTHETIC


def test_format_detection_ulb():
    df = pd.DataFrame({
        "Time": [0.0],
        "V1": [1.2],
        "V2": [-0.5],
        "Amount": [10.0],
        "Class": [0],
    })
    fmt = DatasetLoader.detect_format(df)
    assert fmt == DatasetFormat.ULB


def test_format_detection_ieee():
    df = pd.DataFrame({
        "TransactionID": [3000000],
        "isFraud": [0],
        "TransactionDT": [86400],
        "TransactionAmt": [25.0],
    })
    fmt = DatasetLoader.detect_format(df)
    assert fmt == DatasetFormat.IEEE


def test_chronological_split_no_leakage():
    timestamps = pd.date_range("2026-01-01", periods=100, freq="h", tz="UTC")
    df = pd.DataFrame({
        "timestamp": timestamps,
        "amount": range(100),
        "is_fraud": [0] * 90 + [1] * 10,
    })

    train_df, test_df = DatasetLoader.chronological_split(df, train_ratio=0.8)

    assert len(train_df) == 80
    assert len(test_df) == 20
    # Strict chronological ordering: all train timestamps precede test timestamps
    assert train_df["timestamp"].max() < test_df["timestamp"].min()


def test_stream_event_generator_deterministic(tmp_path):
    gen1 = StreamEventGenerator(seed=123)
    gen2 = StreamEventGenerator(seed=123)

    e1 = gen1.generate_single_event(scenario=ScenarioType.NORMAL)
    e2 = gen2.generate_single_event(scenario=ScenarioType.NORMAL)

    assert e1.amount == e2.amount
    assert e1.synthetic_metadata["scenario"] == "normal"
    assert e1.amount > 0

