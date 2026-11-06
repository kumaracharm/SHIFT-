"""
DRIFTGUARD Configuration Module
Centralized, validated configuration for storage, security, models, and streaming.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Base paths
    BASE_DIR: Path = Path(__file__).resolve().parent
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    SIMULATED_DATA_DIR: Path = DATA_DIR / "simulated"
    KEYS_DIR: Path = BASE_DIR / "keys"
    MODELS_DIR: Path = BASE_DIR / "saved_models"

    # SQLite persistence
    DATABASE_PATH: Path = BASE_DIR / "driftguard.db"
    DATABASE_URL: str = f"sqlite:///{DATABASE_PATH.as_posix()}"

    # Cryptographic Security (Ed25519)
    DEFAULT_KEY_ID: str = "driftguard-primary-key"
    PRIVATE_KEY_FILE: Path = KEYS_DIR / "ed25519_private.pem"
    PUBLIC_KEY_FILE: Path = KEYS_DIR / "ed25519_public.pem"
    MAX_EVENT_AGE_SECONDS: int = 300  # 5 minutes freshness window
    MAX_CLOCK_SKEW_SECONDS: int = 15   # Allow slight forward clock drift

    # Supervised Model Parameters
    RF_N_ESTIMATORS: int = 100
    RF_MAX_DEPTH: int = 12
    RF_RANDOM_STATE: int = 42
    SGD_RANDOM_STATE: int = 42
    TRAIN_SPLIT_RATIO: float = 0.8  # Chronological split

    # Streaming Anomaly Detection (River HalfSpaceTrees)
    HST_N_TREES: int = 25
    HST_HEIGHT: int = 6
    HST_WINDOW_SIZE: int = 200
    HST_SEED: int = 42
    HST_ANOMALY_THRESHOLD: float = 0.65

    # Drift Detection
    ADWIN_DELTA: float = 0.002
    ADWIN_CLOCK: int = 32
    PSI_THRESHOLD_MODERATE: float = 0.10
    PSI_THRESHOLD_HIGH: float = 0.20
    PSI_REFERENCE_WINDOW_SIZE: int = 500
    PSI_STREAM_WINDOW_SIZE: int = 200

    # Decision Engine Thresholds (Validation-Derived)
    THRESHOLD_HIGH_RISK: float = 0.75
    THRESHOLD_REVIEW: float = 0.40
    THRESHOLD_MONITOR: float = 0.20
    VELOCITY_WARNING_COUNT: int = 4   # count within short window
    AMOUNT_ZSCORE_WARNING: float = 3.5

    # Simulation Defaults
    DEFAULT_EVENT_RATE: float = 10.0  # events per second
    SIMULATION_SEED: int = 42

    def ensure_directories(self) -> None:
        """Create standard system directories if they do not exist."""
        for path in [
            self.RAW_DATA_DIR,
            self.PROCESSED_DATA_DIR,
            self.SIMULATED_DATA_DIR,
            self.KEYS_DIR,
            self.MODELS_DIR,
        ]:
            path.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()

