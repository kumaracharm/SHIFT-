"""
DRIFTGUARD Model Registry
Tracks model artifacts, training metrics, versions, and deployment states in SQLite and disk.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from config import settings
from storage.repositories import ModelVersionRepository
from storage.models import ModelVersionRecord
from models.fraud_classifier import SupervisedFraudClassifier


class ModelRegistry:
    """Manages versioned model artifacts and their database metadata records."""

    def __init__(self, session: Session, models_dir: Optional[Path] = None):
        self.session = session
        self.repo = ModelVersionRepository(session)
        self.models_dir = models_dir or settings.MODELS_DIR
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def register_fraud_model(
        self,
        classifier: SupervisedFraudClassifier,
        model_name: str,
        metrics: Dict[str, Any],
        is_active: bool = True,
    ) -> ModelVersionRecord:
        """Saves model artifact to disk and records metadata in database."""
        artifact_path = self.models_dir / f"{classifier.version_id}.joblib"
        classifier.save(artifact_path)

        record = self.repo.register_version(
            version_id=classifier.version_id,
            model_name=model_name,
            model_type="RANDOM_FOREST",
            metrics=metrics,
            filepath=str(artifact_path),
            is_active=is_active,
        )
        return record

    def load_active_fraud_model(self) -> Optional[SupervisedFraudClassifier]:
        """Loads currently active Random Forest model from disk."""
        active_record = self.repo.get_active_version(model_type="RANDOM_FOREST")
        if not active_record or not active_record.filepath:
            return None

        path = Path(active_record.filepath)
        if not path.exists():
            return None

        return SupervisedFraudClassifier.load(path)

    def list_all_models(self) -> List[ModelVersionRecord]:
        """Lists all registered models in the repository."""
        return self.repo.list_versions()

