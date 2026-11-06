"""
DRIFTGUARD Model Laboratory Page
Evaluates supervised classifiers, streaming unsupervised anomaly detectors, and incremental learning candidates.
"""

from datetime import datetime, timezone
import json
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dashboard.components.header import render_header
from dashboard.services.dashboard_service import DashboardService
from dashboard.theme import (
    apply_plotly_theme,
    CARD_BG,
    BORDER_COLOR,
    ACCENT_PRIMARY,
    ACCENT_SECONDARY,
    COLOR_WARNING,
    COLOR_CRITICAL,
    TEXT_MAIN,
    TEXT_MUTED,
)
from config import settings
from storage.database import SessionLocal
from ingestion.dataset_loader import DatasetLoader
from features.feature_pipeline import FeaturePipeline
from models.fraud_classifier import SupervisedFraudClassifier
from models.model_registry import ModelRegistry


def render_model_laboratory_page():
    service = DashboardService()
    health = service.get_system_health()
    model_versions = service.get_model_versions()

    render_header(
        title="MODEL LABORATORY & BENCHMARKS",
        subtitle="Supervised Fraud Baselines, River HalfSpaceTrees Streaming Anomaly & Incremental Retraining",
        system_status="ONLINE" if health["model"]["status"] == "LOADED" else "UNFITTED",
    )

    # Active Model Header
    active_models = [m for m in model_versions if m.get("is_active")]
    active_m = active_models[0] if active_models else None

    # Load detailed evaluation metadata if available
    eval_file = settings.PROCESSED_DATA_DIR / "model_evaluation.json"
    eval_meta = {}
    if eval_file.exists():
        try:
            eval_meta = json.loads(eval_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    c_act1, c_act2 = st.columns([1.8, 1.2])

    with c_act1:
        if active_m:
            metrics = active_m.get("metrics", {})
            ds_name = eval_meta.get("dataset", "IEEE-CIS Fraud Detection" if "ieee" in active_m['version_id'] else "Synthetic Benchmark")
            train_cnt = eval_meta.get("training_samples", 3500)
            holdout_cnt = eval_meta.get("holdout_samples", 750)

            st.markdown(
                f"""
                <div style="background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 8px; padding: 1rem 1.25rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                        <span style="font-size: 0.78rem; font-weight: 700; color: {ACCENT_PRIMARY}; font-family: 'IBM Plex Mono', monospace;">
                            ACTIVE FRAUD CLASSIFIER & BENCHMARK
                        </span>
                        <span style="font-size: 0.72rem; background: rgba(41, 182, 161, 0.15); color: {ACCENT_PRIMARY}; padding: 0.15rem 0.5rem; border-radius: 4px; font-weight: 700;">
                            ACTIVE IN PRODUCTION
                        </span>
                    </div>
                    <div style="font-size: 1.2rem; font-weight: 700; color: #FFFFFF;">
                        {active_m['model_name']} <span style="font-size: 0.85rem; font-family: 'IBM Plex Mono', monospace; color: {TEXT_MUTED};">({active_m['version_id']})</span>
                    </div>
                    <div style="font-size: 0.78rem; color: #D1DDE5; margin-top: 0.3rem;">
                        <b>Dataset Source:</b> <span style="color: {ACCENT_PRIMARY};">{ds_name}</span> | 
                        <b>Train Samples:</b> {train_cnt:,} | <b>Holdout Split:</b> {holdout_cnt:,}
                    </div>
                    <div style="font-size: 0.72rem; color: {TEXT_MUTED}; margin-top: 0.2rem; font-family: 'IBM Plex Mono', monospace;">
                        Trained At: {active_m['trained_at']} | Strict Chronological Evaluation (Zero Lookahead Leakage)
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Imbalance-aware Metrics Row
            st.markdown(f'<div style="margin-top: 0.6rem;"></div>', unsafe_allow_html=True)
            m1, m2, m3, m4, m5 = st.columns(5)
            with m1:
                st.metric("Precision", f"{metrics.get('precision', 0.0):.4f}", "Positive predictive")
            with m2:
                st.metric("Recall", f"{metrics.get('recall', 0.0):.4f}", "True fraud catch rate")
            with m3:
                st.metric("F1-Score", f"{metrics.get('f1', 0.0):.4f}", "Harmonic balance")
            with m4:
                st.metric("PR-AUC", f"{metrics.get('pr_auc', 0.0):.4f}", "Imbalance benchmark")
            with m5:
                st.metric("ROC-AUC", f"{metrics.get('roc_auc', 0.0):.4f}", "Separation power")

            # Confusion Matrix Block
            cm_dict = eval_meta.get("confusion_matrix", {})
            if cm_dict:
                st.markdown(
                    f"""
                    <div style="background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 6px; padding: 0.75rem 1rem; margin-top: 0.6rem; font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem;">
                        <span style="color: {TEXT_MUTED}; font-weight: 700;">HOLDOUT CONFUSION MATRIX:</span> 
                        TN: <b style="color: {ACCENT_PRIMARY};">{cm_dict.get('true_negatives', 0):,}</b> | 
                        FP: <b style="color: {COLOR_WARNING};">{cm_dict.get('false_positives', 0):,}</b> | 
                        FN: <b style="color: {COLOR_CRITICAL};">{cm_dict.get('false_negatives', 0):,}</b> | 
                        TP: <b style="color: {ACCENT_PRIMARY};">{cm_dict.get('true_positives', 0):,}</b>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.warning("No active fraud model currently registered in database.")

    # Domain Integrity & Limitations Notice (PART A Section 3 Requirement)
    st.markdown(
        f"""
        <div style="background-color: rgba(232, 180, 91, 0.08); border-left: 3px solid {COLOR_WARNING}; border-radius: 6px; padding: 0.8rem 1rem; margin-top: 1rem; font-size: 0.76rem; color: #D1DDE5;">
            <b style="color: {COLOR_WARNING};">DOMAIN INTEGRITY & BENCHMARKING POLICY:</b><br>
            • <b>Historical Benchmark:</b> IEEE-CIS represents card-based telemetry (TransactionDT, card1..6, V-features) and serves as the offline supervised ML benchmark.<br>
            • <b>Live Payment Rail:</b> Simulated UPI transactions represent instantaneous mobile-first P2M/P2P transfers with VPA routing and device binding. Operational decisions on UPI streams are governed by transparent multi-signal risk rules and streaming anomaly detection (River HST) to prevent unvalidated cross-domain overfitting.<br>
            • <b>Evaluation Discipline:</b> Synthetic scenario labels are strictly simulation flags and are never presented as real-world fraud ground truth.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with c_act2:
        # Retrain Action Card
        st.markdown(
            f"""
            <div style="background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 8px; padding: 1rem 1.15rem;">
                <div style="font-size: 0.85rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.3rem;">
                    Trigger Controlled Retraining
                </div>
                <div style="font-size: 0.75rem; color: {TEXT_MUTED}; margin-bottom: 0.8rem;">
                    Trains Random Forest with balanced class weighting on chronological split without data leakage.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Train / Register Model Version", key="btn_retrain", type="primary", use_container_width=True):
            with st.spinner("Training Random Forest on chronological benchmark split..."):
                session = SessionLocal()
                try:
                    loader = DatasetLoader()
                    df, fmt = loader.load_dataset()
                    train_df, test_df = loader.chronological_split(df)
                    X_train, y_train = FeaturePipeline.transform_dataframe(train_df)
                    X_test, y_test = FeaturePipeline.transform_dataframe(test_df)
                    clf = SupervisedFraudClassifier(random_state=int(datetime.now().timestamp()) % 1000)
                    clf.fit(X_train, y_train)
                    test_metrics = clf.evaluate(X_test, y_test)
                    reg = ModelRegistry(session)
                    new_rec = reg.register_fraud_model(clf, "RandomForestFraudBaseline", test_metrics, is_active=True)
                    st.success(f"Registered new model version: {new_rec.version_id} (F1: {test_metrics['f1']:.4f})")
                    st.rerun()
                finally:
                    session.close()

    # Model Architecture Comparison Cards
    st.markdown(
        f'<div style="font-size: 1rem; font-weight: 700; color: #FFFFFF; margin-top: 1.25rem; margin-bottom: 0.5rem;">'
        f'Supported Detection Engines & Algorithms</div>',
        unsafe_allow_html=True,
    )

    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        st.markdown(
            f"""
            <div style="background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 6px; padding: 0.85rem; height: 195px;">
                <div style="font-size: 0.75rem; font-weight: 700; color: {ACCENT_PRIMARY}; font-family: 'IBM Plex Mono', monospace;">RANDOM FOREST (RF)</div>
                <div style="font-size: 0.85rem; font-weight: 600; color: #FFFFFF; margin: 0.2rem 0;">Supervised Baseline</div>
                <div style="font-size: 0.72rem; color: #D1DDE5; line-height: 1.4;">
                    • 100 decision trees<br>
                    • Balanced class weights<br>
                    • Probabilistic output [0, 1]<br>
                    • Trained on historical split
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_b:
        st.markdown(
            f"""
            <div style="background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 6px; padding: 0.85rem; height: 195px;">
                <div style="font-size: 0.75rem; font-weight: 700; color: {ACCENT_SECONDARY}; font-family: 'IBM Plex Mono', monospace;">HALF-SPACE TREES (HST)</div>
                <div style="font-size: 0.85rem; font-weight: 600; color: #FFFFFF; margin: 0.2rem 0;">Streaming Anomaly</div>
                <div style="font-size: 0.72rem; color: #D1DDE5; line-height: 1.4;">
                    • River 0.26 streaming engine<br>
                    • Sliding window mass estimates<br>
                    • 25 trees, depth 6<br>
                    • Normalized score [0, 1]
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_c:
        st.markdown(
            f"""
            <div style="background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 6px; padding: 0.85rem; height: 195px;">
                <div style="font-size: 0.75rem; font-weight: 700; color: {COLOR_WARNING}; font-family: 'IBM Plex Mono', monospace;">SGD INCREMENTAL</div>
                <div style="font-size: 0.85rem; font-weight: 600; color: #FFFFFF; margin: 0.2rem 0;">Partial-Fit Adapter</div>
                <div style="font-size: 0.72rem; color: #D1DDE5; line-height: 1.4;">
                    • Log-loss linear classifier<br>
                    • Streaming StandardScaler<br>
                    • Partial-fit gating<br>
                    • Explicit retraining only
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_d:
        st.markdown(
            f"""
            <div style="background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 6px; padding: 0.85rem; height: 195px;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #4DA1A9; font-family: 'IBM Plex Mono', monospace;">ISOLATION FOREST</div>
                <div style="font-size: 0.85rem; font-weight: 600; color: #FFFFFF; margin: 0.2rem 0;">Offline Benchmark</div>
                <div style="font-size: 0.72rem; color: #D1DDE5; line-height: 1.4;">
                    • Scikit-learn baseline<br>
                    • Unsupervised tree isolation<br>
                    • Offline comparison<br>
                    • 2% contamination prior
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Registered Versions Table
    st.markdown(
        f'<div style="font-size: 1rem; font-weight: 700; color: #FFFFFF; margin-top: 1.25rem; margin-bottom: 0.4rem;">'
        f'Model Registry Audit Trail <span style="font-size: 0.8rem; font-weight: 500; color: {TEXT_MUTED};">'
        f'({len(model_versions)} Registered Versions in SQLite)</span></div>',
        unsafe_allow_html=True,
    )

    if model_versions:
        records_df = pd.DataFrame([{
            "version_id": m["version_id"],
            "model_name": m["model_name"],
            "model_type": m["model_type"],
            "trained_at": m["trained_at"].strftime("%Y-%m-%d %H:%M:%S UTC") if hasattr(m["trained_at"], "strftime") else str(m["trained_at"]),
            "is_active": "ACTIVE" if m["is_active"] else "INACTIVE",
            "precision": f"{m['metrics'].get('precision', 0.0):.4f}",
            "recall": f"{m['metrics'].get('recall', 0.0):.4f}",
            "f1": f"{m['metrics'].get('f1', 0.0):.4f}",
            "roc_auc": f"{m['metrics'].get('roc_auc', 0.0):.4f}",
            "pr_auc": f"{m['metrics'].get('pr_auc', 0.0):.4f}",
        } for m in model_versions])

        st.dataframe(
            records_df.rename(columns={
                "version_id": "Version ID",
                "model_name": "Model Name",
                "model_type": "Algorithm",
                "trained_at": "Trained Timestamp",
                "is_active": "Status",
                "precision": "Precision",
                "recall": "Recall",
                "f1": "F1-Score",
                "roc_auc": "ROC-AUC",
                "pr_auc": "PR-AUC",
            }),
            use_container_width=True,
            height=200,
            hide_index=True,
        )

