"""
DRIFTGUARD Feature Pipeline
Integrates transaction and contextual feature extractors into a reproducible, ordered pipeline.
Handles null imputation, bounded state, and feature vector array alignment.
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from ingestion.event_schema import TransactionEvent
from features.transaction_features import TransactionFeatureExtractor
from features.context_features import ContextFeatureExtractor

ORDERED_FEATURE_NAMES: List[str] = [
    "amount",
    "log_amount",
    "amount_zscore",
    "time_since_prev",
    "transaction_velocity",
    "device_consistency",
    "session_consistency",
    "network_risk_flag",
]


class FeaturePipeline:
    """
    Unified streaming and batch feature engineering pipeline.
    Maintains bounded temporal state without future information leakage.
    """

    def __init__(self, history_maxlen: int = 500, max_entities: int = 1000):
        self.tx_extractor = TransactionFeatureExtractor(history_maxlen=history_maxlen)
        self.ctx_extractor = ContextFeatureExtractor(max_entities=max_entities)
        self.feature_names = list(ORDERED_FEATURE_NAMES)

    def extract_features(self, event: TransactionEvent) -> Tuple[Dict[str, float], np.ndarray]:
        """
        Extracts named features and returns both a dictionary and an aligned 1D numpy array.
        """
        tx_feats = self.tx_extractor.extract_features(event)
        ctx_feats = self.ctx_extractor.extract_features(event)

        combined: Dict[str, float] = {**tx_feats, **ctx_feats}

        # Align to strict ordered vector with default fallback imputation
        vector = np.array([float(combined.get(name, 0.0)) for name in self.feature_names], dtype=np.float32)

        return combined, vector

    @classmethod
    def transform_dataframe(cls, df: pd.DataFrame) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Batch extraction for historical benchmark training datasets (ULB, IEEE, Synthetic).
        Ensures identical feature column alignment.
        """
        data_matrix = []
        labels = None

        if "is_fraud" in df.columns:
            labels = df["is_fraud"].to_numpy(dtype=int)

        for _, row in df.iterrows():
            amt = float(row.get("amount", 0.0))
            log_amt = float(np.log1p(amt))
            vel = float(row.get("transaction_velocity", 1.0))
            time_delta = float(row.get("time_since_prev", 300.0))
            dev_cons = float(row.get("device_consistency", 1.0))
            sess_cons = float(row.get("session_consistency", 1.0))
            net_risk = float(row.get("network_risk_flag", 0.0))
            zscore = float(row.get("amount_zscore", 0.0))

            feat_dict = {
                "amount": amt,
                "log_amount": log_amt,
                "amount_zscore": zscore,
                "time_since_prev": time_delta,
                "transaction_velocity": vel,
                "device_consistency": dev_cons,
                "session_consistency": sess_cons,
                "network_risk_flag": net_risk,
            }

            vector = [float(feat_dict.get(name, 0.0)) for name in ORDERED_FEATURE_NAMES]
            data_matrix.append(vector)

        X = np.array(data_matrix, dtype=np.float32)
        return X, labels

