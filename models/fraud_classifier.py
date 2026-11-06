"""
DRIFTGUARD Supervised Fraud Classifiers
Implements:
1. Supervised Random Forest baseline with class-imbalance weighting and comprehensive evaluation metrics.
2. SGDClassifier incremental-learning adapter with partial_fit, feature scaling, and explicit update gating.
"""

from typing import Dict, Any, Tuple, Optional
from pathlib import Path
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
)
from config import settings


class SupervisedFraudClassifier:
    """
    Random Forest fraud classifier trained on labelled chronological transactions.
    Handles class imbalance and produces probabilistic risk scores.
    """

    def __init__(
        self,
        n_estimators: int = settings.RF_N_ESTIMATORS,
        max_depth: int = settings.RF_MAX_DEPTH,
        random_state: int = settings.RF_RANDOM_STATE,
        version_id: Optional[str] = None,
    ):
        self.version_id = version_id or f"rf_v_{random_state}"
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            class_weight="balanced",
            n_jobs=-1,
        )
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Trains the Random Forest and returns training set metrics."""
        self.model.fit(X, y)
        self.is_fitted = True
        return self.evaluate(X, y)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Returns fraud probability for class 1."""
        if not self.is_fitted:
            # Cold start fallback if unfitted
            return np.full(shape=(X.shape[0],), fill_value=0.01, dtype=np.float32)

        # Handle 1D single-sample vector
        if X.ndim == 1:
            X = X.reshape(1, -1)

        # Ensure feature dimension alignment with model expectation
        if hasattr(self.model, "n_features_in_") and X.shape[1] != self.model.n_features_in_:
            if X.shape[1] < self.model.n_features_in_:
                padded = np.zeros((X.shape[0], self.model.n_features_in_), dtype=np.float32)
                padded[:, :X.shape[1]] = X
                X = padded
            else:
                X = X[:, :self.model.n_features_in_]

        probas = self.model.predict_proba(X)
        if probas.shape[1] == 1:
            return np.zeros(shape=(X.shape[0],), dtype=np.float32)
        return probas[:, 1].astype(np.float32)

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """Returns binary predictions based on custom probability threshold."""
        probas = self.predict_proba(X)
        return (probas >= threshold).astype(int)

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Calculates Precision, Recall, F1, ROC-AUC, and PR-AUC."""
        probas = self.predict_proba(X)
        preds = (probas >= 0.5).astype(int)

        precision = float(precision_score(y, preds, zero_division=0))
        recall = float(recall_score(y, preds, zero_division=0))
        f1 = float(f1_score(y, preds, zero_division=0))

        try:
            roc_auc = float(roc_auc_score(y, probas))
        except ValueError:
            roc_auc = 0.5

        try:
            pr_auc = float(average_precision_score(y, probas))
        except ValueError:
            pr_auc = float(np.mean(y))

        return {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "roc_auc": roc_auc,
            "pr_auc": pr_auc,
        }

    def save(self, filepath: Path) -> Path:
        """Persists model artifact to disk."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": self.model, "is_fitted": self.is_fitted, "version_id": self.version_id}, filepath)
        return filepath

    @classmethod
    def load(cls, filepath: Path) -> "SupervisedFraudClassifier":
        """Loads model artifact from disk."""
        data = joblib.load(filepath)
        instance = cls(version_id=data.get("version_id", "unknown"))
        instance.model = data.get("model", data)
        instance.is_fitted = data.get("is_fitted", True)
        return instance


class SGDIncrementalClassifier:
    """
    Incremental linear classifier using SGD with log loss and streaming StandardScaler.
    Maintains class definitions [0, 1] across partial_fit passes.
    """

    def __init__(
        self,
        random_state: int = settings.SGD_RANDOM_STATE,
        version_id: Optional[str] = None,
    ):
        self.version_id = version_id or f"sgd_v_{random_state}"
        self.model = SGDClassifier(
            loss="log_loss",
            penalty="l2",
            alpha=1e-4,
            random_state=random_state,
        )
        self.scaler = StandardScaler()
        self.classes = np.array([0, 1], dtype=int)
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """Initial baseline fit."""
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_fitted = True

    def partial_fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Incremental update on verified batches.
        Requires explicit invocation - never called implicitly on unverified stream data.
        """
        if not self.is_fitted:
            X_scaled = self.scaler.fit_transform(X)
            self.model.partial_fit(X_scaled, y, classes=self.classes)
            self.is_fitted = True
        else:
            self.scaler.partial_fit(X)
            X_scaled = self.scaler.transform(X)
            self.model.partial_fit(X_scaled, y)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Returns probability of fraud class."""
        if not self.is_fitted:
            return np.full(shape=(X.shape[0] if X.ndim > 1 else 1,), fill_value=0.01, dtype=np.float32)

        if X.ndim == 1:
            X = X.reshape(1, -1)

        X_scaled = self.scaler.transform(X)
        probas = self.model.predict_proba(X_scaled)
        return probas[:, 1].astype(np.float32)

