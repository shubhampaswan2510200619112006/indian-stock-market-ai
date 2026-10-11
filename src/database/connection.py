"""
Database connection management.

Supports both PostgreSQL (recommended for production) and SQLite (dev/laptop).
The ORM/repository layer hides database-specific details.
Switch by changing DATABASE_URL in .env.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.utils.config import get_config

_engine = None
_SessionFactory = None


def _get_engine():
    """Create or return the singleton SQLAlchemy engine."""
    global _engine
    if _engine is not None:
        return _engine

    config = get_config()
    url = config.env.database_url

    connect_args = {}
    if url.startswith("sqlite"):
        # Ensure the directory for SQLite file exists
        db_path = url.replace("sqlite:///", "").replace("sqlite:///", "")
        if db_path and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        connect_args = {"check_same_thread": False}

    _engine = create_engine(
        url,
        connect_args=connect_args,
        echo=False,
        pool_pre_ping=True,  # Verify connection liveness
    )

    # Enable WAL mode for SQLite (better concurrent read performance)
    if url.startswith("sqlite"):
        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    # Automatically ensure tables exist on engine initialization (safe, uses CREATE TABLE IF NOT EXISTS)
    try:
        from src.database.models import Base
        Base.metadata.create_all(_engine)
    except Exception:
        pass

    return _engine


def get_session() -> Session:
    """
    Get a new database session.

    Usage:
        session = get_session()
        try:
            # ... do work ...
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    """
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=_get_engine())
    return _SessionFactory()


def init_db() -> None:
    """
    Create all tables. Safe to call multiple times (uses CREATE IF NOT EXISTS).
    """
    from src.database.models import Base
    engine = _get_engine()
    Base.metadata.create_all(engine)


def get_engine():
    """Public access to the engine (for Alembic, testing, etc.)."""
    return _get_engine()
