"""
Database connection management.

Supports both PostgreSQL (recommended for production) and SQLite (dev/laptop).
The ORM/repository layer hides database-specific details.
Switch by changing DATABASE_URL in .env.

Production Safety Invariant:
Never silently fall back from configured PostgreSQL to ephemeral SQLite.
If PostgreSQL is configured, connectivity is validated on startup and fails loud.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from src.utils.config import get_config

logger = logging.getLogger(__name__)

_engine = None
_SessionFactory = None


class DatabaseConfig:
    """Explicit database configuration and production environment validator."""

    def __init__(self, url: str, is_production: bool = False, pool_size: int = 10, max_overflow: int = 20):
        self.url = url
        self.is_production = is_production
        self.pool_size = pool_size
        self.max_overflow = max_overflow

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        env = os.getenv("ENVIRONMENT") or os.getenv("APP_ENV", "development")
        is_prod = env.lower() in ("production", "prod")
        url = os.getenv("DATABASE_URL")
        if not url:
            try:
                url = get_config().env.database_url
            except Exception:
                url = "sqlite:///data/options_intel.db"

        if is_prod and (not url or url.startswith("sqlite")):
            raise RuntimeError(
                "Production environment requires a managed PostgreSQL database (e.g. Supabase, Neon, AWS RDS, Railway). "
                "Silent fallback to ephemeral SQLite is strictly prohibited."
            )

        return cls(
            url=url,
            is_production=is_prod,
            pool_size=10 if is_prod else 5,
            max_overflow=20 if is_prod else 10,
        )


def _get_engine():
    """Create or return the singleton SQLAlchemy engine."""
    global _engine
    if _engine is not None:
        return _engine

    db_config = DatabaseConfig.from_env()
    url = db_config.url

    connect_args = {}

    # 1. PostgreSQL (Production standard)
    if "postgresql" in url or "postgres" in url:
        # Standardize modern SQLAlchemy driver URI
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)

        logger.info("Initializing production PostgreSQL connection pool...")
        _engine = create_engine(
            url,
            pool_size=10,
            max_overflow=20,
            pool_recycle=1800,
            pool_pre_ping=True,
            pool_timeout=30,
            echo=False,
        )

        # STRICT SAFETY GATE: Validate connection immediately at startup
        # Never silently fall back to ephemeral SQLite if PostgreSQL fails!
        try:
            with _engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Production PostgreSQL connection successfully verified.")
        except Exception as e:
            logger.critical(f"FATAL: Production PostgreSQL connection failed: {e}")
            raise RuntimeError(
                f"Production database connection failed: {e}. "
                "Silent fallback to ephemeral SQLite is disabled in accordance with production safety invariants."
            ) from e

    # 2. SQLite (Development, local laptop, and isolated tests)
    elif url.startswith("sqlite"):
        if os.getenv("APP_ENV") == "production":
            logger.warning(
                "NOTICE: Running in production with SQLite storage. Local filesystem may be ephemeral on container hosts."
            )

        db_path = url.replace("sqlite:///", "").replace("sqlite:///", "")
        if db_path and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        connect_args = {"check_same_thread": False}

        _engine = create_engine(
            url,
            connect_args=connect_args,
            echo=False,
            pool_pre_ping=True,
        )

        # Enable WAL mode for SQLite (better concurrent read/write performance)
        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    else:
        # Generic engine fallback
        _engine = create_engine(url, echo=False, pool_pre_ping=True)

    # Automatically ensure tables exist on engine initialization
    try:
        from src.database.models import Base
        Base.metadata.create_all(_engine)
    except Exception as e:
        logger.warning(f"Metadata create_all notice: {e}")

    return _engine


def get_session() -> Session:
    """
    Get a new database session with explicit transaction boundaries.

    Usage:
        session = get_session()
        try:
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


def check_db_health() -> Dict[str, Any]:
    """Tests database connectivity and reports health metrics for health endpoints."""
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        from src.database.models import Base
        return {
            "status": "healthy",
            "dialect": engine.dialect.name,
            "connected": True,
            "table_count": len(Base.metadata.tables),
            "pool_status": {
                "size": getattr(engine.pool, "size", lambda: None)(),
                "checked_in": getattr(engine.pool, "checkedin", lambda: None)(),
                "checked_out": getattr(engine.pool, "checkedout", lambda: None)(),
            } if hasattr(engine, "pool") else None,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e),
        }


def get_engine(url: Optional[str] = None):
    """Public access to the engine (for Alembic, testing, etc.)."""
    if url:
        return create_engine(url)
    return _get_engine()


def reset_engine() -> None:
    """Reset singleton engine and session factory (primarily for tests)."""
    global _engine, _SessionFactory
    if _engine is not None:
        try:
            _engine.dispose()
        except Exception:
            pass
    _engine = None
    _SessionFactory = None
