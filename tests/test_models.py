"""
DRIFTGUARD Model Tests
Verifies Random Forest baseline, SGD incremental adapter, River HalfSpaceTrees streaming anomaly detector,
and Isolation Forest offline baseline.
"""

from pathlib import Path
import numpy as np
import pytest
from models.fraud_classifier import SupervisedFraudClassifier, SGDIncrementalClassifier
from models.anomaly_detector import StreamingAnomalyDetector, IsolationForestBaseline


@pytest.fixture
def dummy_data():
    rng = np.random.default_rng(42)
    n_samples = 400
    n_features = 8

    # Normal samples
    X_normal = rng.normal(loc=0.0, scale=1.0, size=(380, n_features))
    y_normal = np.zeros(380, dtype=int)

    # Fraud samples (elevated feature values)
    X_fraud = rng.normal(loc=3.0, scale=1.0, size=(20, n_features))
    y_fraud = np.ones(20, dtype=int)

    X = np.vstack([X_normal, X_fraud]).astype(np.float32)
    y = np.concatenate([y_normal, y_fraud])

    indices = rng.permutation(n_samples)
    return X[indices], y[indices]


def test_random_forest_training_and_metrics(dummy_data, tmp_path):
    X, y = dummy_data
    clf = SupervisedFraudClassifier(n_estimators=30, random_state=42)
    metrics = clf.fit(X, y)

    assert clf.is_fitted is True
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1" in metrics
    assert "pr_auc" in metrics

    probas = clf.predict_proba(X)
    assert len(probas) == len(X)
    assert (probas >= 0.0).all() and (probas <= 1.0).all()

    # Save and reload
    model_path = tmp_path / "rf_test.joblib"
    clf.save(model_path)
    loaded = SupervisedFraudClassifier.load(model_path)
    assert loaded.is_fitted is True
    assert loaded.version_id == clf.version_id


def test_sgd_incremental_classifier(dummy_data):
    X, y = dummy_data
    sgd = SGDIncrementalClassifier(random_state=42)

    # Initial batch fit
    sgd.fit(X[:200], y[:200])
    assert sgd.is_fitted is True

    # Incremental update via partial_fit
    sgd.partial_fit(X[200:], y[200:])
    probas = sgd.predict_proba(X)
    assert len(probas) == len(X)
    assert (probas >= 0.0).all() and (probas <= 1.0).all()


def test_river_half_space_trees_streaming():
    hst = StreamingAnomalyDetector(n_trees=15, height=6, window_size=50, seed=42)

    # Feed baseline observations
    rng = np.random.default_rng(42)
    for _ in range(80):
        normal_feat = {
            "amount": float(rng.normal(50.0, 10.0)),
            "log_amount": float(np.log1p(50.0)),
            "amount_zscore": 0.1,
            "time_since_prev": 60.0,
            "transaction_velocity": 1.0,
            "device_consistency": 1.0,
            "session_consistency": 1.0,
            "network_risk_flag": 0.0,
        }
        hst.learn_one(normal_feat)

    assert hst.observation_count == 80

    # Normal observation should have moderate/low score
    normal_score = hst.score_one({
        "amount": 52.0,
        "log_amount": float(np.log1p(52.0)),
        "amount_zscore": 0.2,
        "time_since_prev": 55.0,
        "transaction_velocity": 1.0,
        "device_consistency": 1.0,
        "session_consistency": 1.0,
        "network_risk_flag": 0.0,
    })

    # Outlier observation with extreme values
    outlier_score = hst.score_one({
        "amount": 4900.0,
        "log_amount": float(np.log1p(4900.0)),
        "amount_zscore": 8.5,
        "time_since_prev": 2.0,
        "transaction_velocity": 15.0,
        "device_consistency": 0.0,
        "session_consistency": 0.5,
        "network_risk_flag": 1.0,
    })

    assert outlier_score >= normal_score
    assert 0.0 <= normal_score <= 1.0
    assert 0.0 <= outlier_score <= 1.0


def test_isolation_forest_baseline(dummy_data):
    X, _ = dummy_data
    iso = IsolationForestBaseline(random_state=42)
    iso.fit(X)
    assert iso.is_fitted is True

    scores = iso.score_samples(X)
    assert len(scores) == len(X)
    assert (scores >= 0.0).all() and (scores <= 1.0).all()

