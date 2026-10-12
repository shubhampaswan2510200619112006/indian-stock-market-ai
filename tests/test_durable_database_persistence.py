"""
Integration tests for durable database storage and multi-user isolation.

Verifies:
1. Database state persistence (UserPaperStateDB) across simulated container restarts.
2. Complete recovery of portfolio cash, positions, orders, and fills from database when disk state is wiped.
3. Multi-user state isolation (User A cannot see or mutate User B's state).
4. Production PostgreSQL configuration enforcement (no silent fallback).
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
import pytest

from src.database.connection import DatabaseConfig, get_engine, get_session, reset_engine
from src.database.models import Base, UserPaperStateDB
from src.paper_trading.models import PaperOrderSide, PaperOrderType
from src.paper_trading.service import PaperTradingService


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path):
    """Set up an isolated SQLite test database and tables."""
    test_db_path = tmp_path / "test_durable.db"
    test_db_url = f"sqlite:///{test_db_path}"
    os.environ["DATABASE_URL"] = test_db_url
    reset_engine()

    engine = get_engine(test_db_url)
    Base.metadata.create_all(engine)

    yield test_db_url

    reset_engine()
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]


def test_durable_state_recovery_after_disk_wipe(tmp_path):
    """
    Simulates container redeploy/restart where disk JSON files are wiped,
    confirming state is restored purely from UserPaperStateDB.
    """
    user_id = "trader_prod_99"
    state_dir = tmp_path / "ephemeral_disk" / user_id

    # 1. Start service with initial capital and place simulated order
    svc = PaperTradingService(
        initial_capital=5_000_000.0,
        state_dir=str(state_dir),
        user_id=user_id,
    )
    # Enable off hours simulation for test order
    svc.fill_engine.allow_off_hours_simulation = True

    # Place an order that generates state within risk bounds
    result = svc.place_order(
        symbol="NIFTY",
        side="BUY",
        quantity=1,
        order_type="LIMIT",
        limit_price=100.0,
    )
    assert result["status"] in ("FILLED", "OPEN", "SUBMITTED")

    # Manually save state to ensure DB and disk are synced
    svc.save_state()

    # Verify DB record exists
    with get_session() as session:
        record = session.query(UserPaperStateDB).filter_by(user_id=user_id).first()
        assert record is not None
        assert record.portfolio_state is not None
        assert "cash" in record.portfolio_state

    # 2. Simulate container recreation: completely delete the disk state directory!
    shutil.rmtree(state_dir)
    assert not state_dir.exists()

    # 3. Instantiate fresh service on new empty directory with auto_restore=True
    new_dir = tmp_path / "new_container_disk" / user_id
    recovered_svc = PaperTradingService(
        initial_capital=5_000_000.0,
        state_dir=str(new_dir),
        user_id=user_id,
        auto_restore=True,
    )

    # 4. Verify portfolio recovered from database rather than resetting to default starting capital
    recovered_cash = recovered_svc.portfolio.cash
    assert recovered_cash == svc.portfolio.cash
    assert len(recovered_svc.order_manager.get_all_orders()) == len(svc.order_manager.get_all_orders())
    assert len(recovered_svc._all_fills) == len(svc._all_fills)


def test_multi_user_paper_state_isolation(tmp_path):
    """
    Verifies that two distinct authenticated users have completely isolated state
    both in memory and in the persistent database.
    """
    user_a = "user_alpha"
    user_b = "user_beta"

    svc_a = PaperTradingService(
        initial_capital=100_000.0,
        state_dir=str(tmp_path / user_a),
        user_id=user_a,
    )
    svc_b = PaperTradingService(
        initial_capital=2_000_000.0,
        state_dir=str(tmp_path / user_b),
        user_id=user_b,
    )

    svc_a.fill_engine.allow_off_hours_simulation = True
    svc_b.fill_engine.allow_off_hours_simulation = True

    # Order on user A only
    svc_a.place_order(
        symbol="NIFTY",
        side="BUY",
        quantity=50,
        order_type="MARKET",
        limit_price=24000.0,
    )
    svc_a.save_state()
    svc_b.save_state()

    # Query database records directly
    with get_session() as session:
        db_a = session.query(UserPaperStateDB).filter_by(user_id=user_a).first()
        db_b = session.query(UserPaperStateDB).filter_by(user_id=user_b).first()

        assert db_a is not None
        assert db_b is not None
        # User A has orders, User B does not
        assert len(db_a.orders_state) >= 1
        assert len(db_b.orders_state) == 0
        # Capital remains isolated
        assert db_b.portfolio_state["initial_capital"] == 2_000_000.0


def test_production_postgresql_config_validation(monkeypatch):
    """
    Verifies that when ENVIRONMENT=production:
    1. If DATABASE_URL is SQLite, validation raises RuntimeError (no silent fallback).
    2. If DATABASE_URL is PostgreSQL, validation passes with pool settings.
    """
    monkeypatch.setenv("ENVIRONMENT", "production")

    # 1. SQLite in production must raise RuntimeError
    monkeypatch.setenv("DATABASE_URL", "sqlite:///ephemeral.db")
    with pytest.raises(RuntimeError, match="Production environment requires a managed PostgreSQL database"):
        DatabaseConfig.from_env()

    # 2. Managed PostgreSQL in production must succeed with pooling
    monkeypatch.setenv("DATABASE_URL", "postgresql://prod_user:secret@db.internal:5432/trading_db")
    config = DatabaseConfig.from_env()
    assert config.is_production is True
    assert config.pool_size == 10
    assert config.max_overflow == 20
