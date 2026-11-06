"""
DRIFTGUARD 2.0 System & Settings Router
"""

from fastapi import APIRouter
from typing import Dict, Any
from pathlib import Path
from sqlalchemy import func
from storage.database import SessionLocal
from storage.models import (
    EventRecord,
    PredictionRecord,
    IntegrityLogRecord,
    ReplayProtectionRecord,
    DriftEventRecord,
    ModelVersionRecord,
)
from security.key_manager import KeyManager
from config import settings

router = APIRouter(prefix="/api/v1/system", tags=["System"])


@router.get("/health")
def get_system_health() -> Dict[str, Any]:
    """Provides system health verification and operational status."""
    db_ok = False
    session = SessionLocal()
    try:
        session.query(func.count(EventRecord.event_id)).scalar()
        db_ok = True
    except Exception:
        db_ok = False
    finally:
        session.close()

    km = KeyManager()
    has_key = km.get_public_key(settings.DEFAULT_KEY_ID) is not None

    return {
        "status": "healthy" if db_ok and has_key else "degraded",
        "database_connected": db_ok,
        "cryptographic_key_loaded": has_key,
        "default_key_id": settings.DEFAULT_KEY_ID,
        "algorithm": "Ed25519",
        "environment": "Production / Demonstration",
    }


@router.get("/keys")
def get_key_status() -> Dict[str, Any]:
    """Provides Ed25519 digital signature key infrastructure status."""
    km = KeyManager()
    pub_key_path = settings.KEYS_DIR / f"{settings.DEFAULT_KEY_ID}_public.pem"
    priv_key_path = settings.KEYS_DIR / f"{settings.DEFAULT_KEY_ID}_private.pem"

    return {
        "status": "success",
        "default_key_id": settings.DEFAULT_KEY_ID,
        "algorithm": "Ed25519 (RFC 8032)",
        "public_key_present": pub_key_path.exists(),
        "private_key_present": priv_key_path.exists(),
        "key_directory": str(settings.KEYS_DIR),
        "replay_cache_window_seconds": settings.MAX_EVENT_AGE_SECONDS,
    }


@router.get("/db-stats")
def get_db_stats() -> Dict[str, Any]:
    """Retrieves SQLite database storage volume and table record counts."""
    db_path = Path("driftguard.db")
    size_mb = round(db_path.stat().st_size / (1024 * 1024), 2) if db_path.exists() else 0.0

    session = SessionLocal()
    try:
        events_cnt = session.query(func.count(EventRecord.event_id)).scalar() or 0
        preds_cnt = session.query(func.count(PredictionRecord.id)).scalar() or 0
        integrity_cnt = session.query(func.count(IntegrityLogRecord.id)).scalar() or 0
        replay_cnt = session.query(func.count(ReplayProtectionRecord.id)).scalar() or 0
        drift_cnt = session.query(func.count(DriftEventRecord.id)).scalar() or 0
        models_cnt = session.query(func.count(ModelVersionRecord.version_id)).scalar() or 0

        return {
            "status": "success",
            "database_file": str(db_path.resolve()),
            "size_mb": size_mb,
            "counts": {
                "events": events_cnt,
                "predictions": preds_cnt,
                "integrity_logs": integrity_cnt,
                "replay_cache": replay_cnt,
                "drift_events": drift_cnt,
                "model_versions": models_cnt,
            },
        }
    finally:
        session.close()
