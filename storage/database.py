"""
DRIFTGUARD Database Management
Provides thread-safe session factories, engine creation, and schema initialization.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import settings
from storage.models import Base

# Engine configuration - SQLite needs check_same_thread=False for multi-threaded or testing contexts
def get_engine(db_url: str = settings.DATABASE_URL):
    return create_engine(
        db_url,
        connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {},
        echo=False
    )

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(db_engine=None) -> None:
    """Initialize database tables according to defined ORM models."""
    target_engine = db_engine or engine
    Base.metadata.create_all(bind=target_engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency / context generator for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

