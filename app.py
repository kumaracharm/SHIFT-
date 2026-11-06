"""
DRIFTGUARD Application CLI Entry Point
Adaptive Streaming Fraud and Threat Detection System.
Provides command-line interfaces for database setup, model training,
streaming simulation scenarios, security attack verification, and telemetry audits.
"""

import argparse
import sys
from datetime import datetime, timezone
import json
from config import settings
from storage.database import engine, init_db, SessionLocal
from storage.repositories import (
    EventRepository,
    PredictionRepository,
    IntegrityLogRepository,
    DriftRepository,
    ModelVersionRepository,
)
from security.key_manager import KeyManager
from ingestion.dataset_loader import DatasetLoader
from features.feature_pipeline import FeaturePipeline
from models.fraud_classifier import SupervisedFraudClassifier
from models.anomaly_detector import StreamingAnomalyDetector
from models.prediction_service import PredictionService
from models.model_registry import ModelRegistry
from drift.drift_manager import DriftManager
from engine.event_service import EventProcessingService
from simulation.scenarios import ScenarioType
from simulation.experiment_runner import ExperimentRunner
from ingestion.event_generator import StreamEventGenerator


def cmd_init_db(args):
    """Initializes SQLite schema and generates primary Ed25519 signing keypair."""
    print("=" * 60)
    print("DRIFTGUARD: Initializing Storage and Cryptographic Keystore")
    print("=" * 60)
    init_db(engine)
    print(f" SQLite schema created at: {settings.DATABASE_PATH}")

    km = KeyManager()
    priv, pub = km.load_or_create_default_key(settings.DEFAULT_KEY_ID)
    print(f" Primary Ed25519 key registered: {settings.DEFAULT_KEY_ID}")
    print(f" Private key stored at: {settings.KEYS_DIR}")
    print("[OK] Initialization complete.\n")


def cmd_train(args):
    """Trains baseline Random Forest model on historical/synthetic dataset and registers it."""
    print("=" * 60)
    print("DRIFTGUARD: Training Supervised Fraud Detection Baseline")
    print("=" * 60)
    init_db(engine)
    session = SessionLocal()
    try:
        loader = DatasetLoader()
        df, fmt = loader.load_dataset(filepath=args.dataset_path)
        print(f" Loaded dataset with {len(df)} records. Format: {fmt.upper()}")

        train_df, test_df = loader.chronological_split(df)
        print(f" Chronological Split: {len(train_df)} training samples, {len(test_df)} testing samples.")

        X_train, y_train = FeaturePipeline.transform_dataframe(train_df)
        X_test, y_test = FeaturePipeline.transform_dataframe(test_df)

        print(f" Extracted {X_train.shape[1]} feature dimensions.")
        print(" Fitting Random Forest with balanced class weighting...")

        clf = SupervisedFraudClassifier(random_state=settings.RF_RANDOM_STATE)
        clf.fit(X_train, y_train)

        test_metrics = clf.evaluate(X_test, y_test)
        print("\n=== Model Evaluation (Chronological Test Split) ===")
        print(f"  Precision : {test_metrics['precision']:.4f}")
        print(f"  Recall    : {test_metrics['recall']:.4f}")
        print(f"  F1-Score  : {test_metrics['f1']:.4f}")
        print(f"  ROC-AUC   : {test_metrics['roc_auc']:.4f}")
        print(f"  PR-AUC    : {test_metrics['pr_auc']:.4f}")

        registry = ModelRegistry(session)
        record = registry.register_fraud_model(
            classifier=clf,
            model_name="RandomForestFraudBaseline",
            metrics=test_metrics,
            is_active=True,
        )
        print(f"\n Registered active model version: {record.version_id}")
        print("[OK] Training complete.\n")
    finally:
        session.close()


def cmd_stream(args):
    """Executes a streaming simulation scenario through the complete processing pipeline."""
    scenario_str = args.scenario.lower()
    try:
        scenario = ScenarioType(scenario_str)
    except ValueError:
        valid_scenarios = [s.value for s in ScenarioType]
        print(f"Error: Unknown scenario '{args.scenario}'. Choose from: {valid_scenarios}")
        sys.exit(1)

    print("=" * 60)
    print(f"DRIFTGUARD: Streaming Scenario Execution [{scenario.value.upper()}]")
    print("=" * 60)

    init_db(engine)
    session = SessionLocal()
    try:
        # Load or train classifier
        registry = ModelRegistry(session)
        clf = registry.load_active_fraud_model()
        if clf is None:
            print(" No registered active model found. Training default baseline first...")
            loader = DatasetLoader()
            df, _ = loader.load_dataset()
            train_df, test_df = loader.chronological_split(df)
            X_train, y_train = FeaturePipeline.transform_dataframe(train_df)
            X_test, y_test = FeaturePipeline.transform_dataframe(test_df)
            clf = SupervisedFraudClassifier()
            clf.fit(X_train, y_train)
            metrics = clf.evaluate(X_test, y_test)
            registry.register_fraud_model(clf, "AutoTrainedBaseline", metrics, is_active=True)

        pred_service = PredictionService(fraud_classifier=clf)
        service = EventProcessingService(
            session=session,
            prediction_service=pred_service,
            enforce_freshness=not args.ignore_freshness,
        )

        runner = ExperimentRunner(session=session, event_service=service)
        summary = runner.run_scenario(
            scenario=scenario,
            total_events=args.count,
            anomaly_ratio=args.anomaly_ratio,
        )

        print("\n=== Scenario Run Summary ===")
        print(f" Scenario         : {summary['scenario']}")
        print(f" Total Events     : {summary['total_events']}")
        print(f" Rejected (Sec)   : {summary['rejected_events']}")
        print(f" Flagged (Fraud)  : {summary['flagged_events']}")
        print(f" Duration (sec)   : {summary['duration_seconds']}s")
        print(f" Throughput       : {summary['events_per_second']} events/sec")
        print(f" Decisions        : {json.dumps(summary['decision_breakdown'], indent=2)}")
        print("[OK] Stream execution complete.\n")
    finally:
        session.close()


def cmd_verify_security(args):
    """Executes explicit cryptographic tamper and replay attack verifications."""
    print("=" * 60)
    print("DRIFTGUARD: Security & Cryptographic Boundary Verification")
    print("=" * 60)
    init_db(engine)
    session = SessionLocal()
    try:
        km = KeyManager()
        km.load_or_create_default_key(settings.DEFAULT_KEY_ID)
        generator = StreamEventGenerator(key_manager=km)
        service = EventProcessingService(session=session, key_manager=km)

        # 1. Valid Event Test
        print("\n[1] Testing Valid Cryptographically Signed Event...")
        valid_evt = generator.generate_single_event(scenario=ScenarioType.NORMAL)
        res1 = service.process_event(valid_evt)
        print(f"  Decision: {res1.decision} | Integrity: {res1.integrity_status}")
        assert res1.decision != "INTEGRITY_REJECTED", "Valid event was unexpectedly rejected!"
        print("   Valid event successfully accepted.")

        # 2. Tampered Payload / Signature Attack Test
        print("\n[2] Testing Tampered Payload Attack (Man-in-the-Middle)...")
        tampered_evt = generator.generate_single_event(scenario=ScenarioType.NORMAL, tamper_signature=True)
        res2 = service.process_event(tampered_evt)
        print(f"  Decision: {res2.decision} | Integrity: {res2.integrity_status}")
        assert res2.decision == "INTEGRITY_REJECTED", "Tampered event was not rejected!"
        print("   Tampered payload successfully intercepted and rejected.")

        # 3. Replay Attack Test (Same Nonce and Event ID)
        print("\n[3] Testing Replay Attack (Duplicate Event ID & Nonce)...")
        res3 = service.process_event(valid_evt)  # resend valid event
        print(f"  Decision: {res3.decision} | Integrity: {res3.integrity_status}")
        assert res3.decision == "INTEGRITY_REJECTED", "Replayed event was not rejected!"
        print("   Replay attack successfully intercepted and rejected.")

        print("\n[OK] All security integrity barriers verified.\n")
    finally:
        session.close()


def cmd_status(args):
    """Displays current SQLite persistence records, drift alerts, and integrity logs."""
    init_db(engine)
    session = SessionLocal()
    try:
        event_repo = EventRepository(session)
        pred_repo = PredictionRepository(session)
        log_repo = IntegrityLogRepository(session)
        drift_repo = DriftRepository(session)
        model_repo = ModelVersionRepository(session)

        events = event_repo.list_events(limit=5)
        predictions = pred_repo.list_predictions(limit=5)
        logs = log_repo.list_logs(limit=5)
        drifts = drift_repo.list_drift_events(limit=5)
        models = model_repo.list_versions()

        print("=" * 60)
        print("DRIFTGUARD: Persistence and Telemetry Status")
        print("=" * 60)
        print(f" Active Models Registered: {len(models)}")
        for m in models:
            print(f"  - [{m.version_id}] {m.model_name} (active={m.is_active})")

        print(f"\n Recent Integrity Logs: {len(logs)} shown")
        for l in logs:
            print(f"  - Event: {l.event_id[:12]}.. | Status: {l.status} | Reason: {l.reason[:40]}")

        print(f"\n Recent Predictions: {len(predictions)} shown")
        for p in predictions:
            print(f"  - Event: {p.event_id[:12]}.. | Decision: {p.decision} | FraudProb: {p.fraud_probability:.2f} | AnomScore: {p.anomaly_score:.2f}")

        print(f"\n Drift Events Recorded: {len(drifts)} shown")
        for d in drifts:
            print(f"  - [{d.detector_name}] Signal: {d.signal_type} | Obs: {d.observation_count} | Metric: {d.metric_value:.4f}")

        print("\n[OK] Status reported.\n")
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(
        description="DRIFTGUARD: Adaptive Streaming Fraud & Threat Detection Engine",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Operational Subcommands")

    # init-db
    subparsers.add_parser("init-db", help="Initialize SQLite tables and cryptographic keys")

    # train
    train_p = subparsers.add_parser("train", help="Train baseline supervised fraud classifier")
    train_p.add_argument("--dataset-path", type=str, default=None, help="Path to CSV dataset")

    # stream
    stream_p = subparsers.add_parser("stream", help="Run a streaming transaction simulation scenario")
    stream_p.add_argument("--scenario", type=str, default="normal", help="Scenario name (normal, amount_spike, velocity_burst, etc.)")
    stream_p.add_argument("--count", type=int, default=50, help="Number of streaming events to generate")
    stream_p.add_argument("--anomaly-ratio", type=float, default=0.1, help="Ratio of injected anomalies")
    stream_p.add_argument("--ignore-freshness", action="store_true", help="Bypass timestamp freshness for historical replay")

    # verify-security
    subparsers.add_parser("verify-security", help="Verify cryptographic signature and replay protections")

    # status
    subparsers.add_parser("status", help="Print summary of database records and telemetry")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "init-db": cmd_init_db,
        "train": cmd_train,
        "stream": cmd_stream,
        "verify-security": cmd_verify_security,
        "status": cmd_status,
    }

    cmd_fn = dispatch.get(args.command)
    if cmd_fn:
        cmd_fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

