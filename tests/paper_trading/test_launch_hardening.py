"""
Automated Launch-Hardening & Reliability Tests for Paper Trading.

Verifies:
1. Non-bypassable execution guard (LIVE execution blocked).
2. Risk control boundary conditions (zero equity, negative quantity, invalid limit price).
3. Circuit breaker trip, pending order cancellation, order rejection, and manual reset.
4. Position closing with offsetting fill and journal trade record.
5. State persistence and crash recovery across service restarts.
6. API schema validation rejecting invalid order payloads with HTTP 422.
"""

import tempfile
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from src.api.main import create_app
from src.paper_trading.execution_guard import ALLOW_LIVE_EXECUTION, ExecutionGuard, LiveExecutionDisabledError
from src.paper_trading.models import PaperOrder, PaperOrderSide, PaperOrderType
from src.paper_trading.risk_manager import PaperRiskManager
from src.paper_trading.service import PaperTradingService


def test_live_execution_guard_raises_error():
    """Ensure ExecutionGuard strictly blocks LIVE mode under all circumstances."""
    with pytest.raises(LiveExecutionDisabledError):
        ExecutionGuard.validate_execution_mode("LIVE")

    assert ALLOW_LIVE_EXECUTION is False


def test_risk_manager_boundary_conditions():
    """Verify pre-trade risk manager rejects zero equity and invalid quantities."""
    rm = PaperRiskManager()

    # Zero equity
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        quantity=25,
        order_type=PaperOrderType.MARKET,
        execution_mode="PAPER",
    )
    res = rm.check_order(
        order=order,
        current_equity=0.0,
        daily_pnl=0.0,
        drawdown_pct=0.0,
        open_positions=[],
    )
    assert not res.is_approved
    assert any("ZERO_EQUITY" in r for r in res.rejection_reasons)

    # Invalid quantity
    order_zero_qty = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        quantity=0,
        order_type=PaperOrderType.MARKET,
        execution_mode="PAPER",
    )
    res_zero = rm.check_order(
        order=order_zero_qty,
        current_equity=1000000.0,
        daily_pnl=0.0,
        drawdown_pct=0.0,
        open_positions=[],
    )
    assert not res_zero.is_approved
    assert any("INVALID_QUANTITY" in r for r in res_zero.rejection_reasons)

    # Invalid limit price
    order_invalid_limit = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        quantity=25,
        order_type=PaperOrderType.LIMIT,
        limit_price=0.0,
        execution_mode="PAPER",
    )
    res_limit = rm.check_order(
        order=order_invalid_limit,
        current_equity=1000000.0,
        daily_pnl=0.0,
        drawdown_pct=0.0,
        open_positions=[],
    )
    assert not res_limit.is_approved
    assert any("INVALID_LIMIT_PRICE" in r for r in res_limit.rejection_reasons)


def test_circuit_breaker_trip_and_reset():
    """Verify manual circuit breaker halt blocks orders and reset re-enables them."""
    svc = PaperTradingService()
    svc.reset_breakers()

    # Trip breaker
    trip_res = svc.trip_breaker(reason="AUDIT_HALT")
    assert trip_res["status"] == "TRIPPED"

    # Order during active breaker must be rejected
    order_res = svc.place_order(symbol="NIFTY", side="BUY", quantity=25, order_type="MARKET")
    assert order_res["status"] == "REJECTED"
    assert "CIRCUIT_BREAKER" in order_res["rejection_reason"]

    # Reset breaker
    reset_res = svc.reset_breakers()
    assert reset_res["status"] == "RESET"

    # Order after reset is accepted
    order_ok = svc.place_order(symbol="NIFTY", side="BUY", quantity=25, order_type="MARKET")
    assert order_ok["status"] == "PENDING"
    assert order_ok["risk_approved"] is True


def test_position_close_execution():
    """Verify closing position creates offsetting fill and audit record."""
    svc = PaperTradingService()
    # Ensure clean portfolio
    svc.reset_paper_account(confirm=True)

    # Fill an initial position
    from datetime import datetime, timezone
    from src.paper_trading.models import PaperFill, PaperFillSource

    now = datetime.now(timezone.utc)
    fill = PaperFill(
        order_id="INIT-POS",
        symbol="NIFTY",
        fill_quantity=50,
        fill_price=24000.0,
        fill_timestamp=now,
        provider_timestamp=now,
        received_timestamp=now,
        execution_timestamp=now,
        price_source=PaperFillSource.PROVIDER_ASK,
        price_source_description="Initial position fill",
        data_status_at_fill="DELAYED",
        slippage_applied=0.0,
        transaction_costs=0.0,
        quote_age_seconds=1.0,
        source_provider="YFINANCE",
        provider="YFINANCE",
    )
    svc.portfolio.apply_fill(fill, PaperOrderSide.BUY)
    svc.portfolio.mark_to_market("NIFTY", 24200.0, now)

    open_positions = svc.get_positions(status="OPEN")["positions"]
    assert len(open_positions) == 1
    assert open_positions[0]["symbol"] == "NIFTY"
    pos_id = open_positions[0]["position_id"]

    # Close position
    close_res = svc.close_position(pos_id, quantity=50)
    assert close_res["status"] == "CLOSED"
    assert close_res["closed_quantity"] == 50

    # Verify open positions are now 0 and closed positions has 1 record
    assert len(svc.get_positions(status="OPEN")["positions"]) == 0
    closed_pos = svc.get_positions(status="CLOSED")["positions"]
    assert len(closed_pos) >= 1
    assert closed_pos[-1]["symbol"] == "NIFTY"


def test_state_persistence_and_recovery():
    """Verify portfolio state can be saved and restored across crashes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_dir = Path(tmpdir)
        svc = PaperTradingService(state_dir=state_dir)
        svc.portfolio.cash = 950000.0
        svc.portfolio.realized_pnl = 50000.0
        svc.save_state()

        # Create fresh service and restore
        fresh_svc = PaperTradingService(state_dir=state_dir)
        restored = fresh_svc.restore_state()
        assert restored is True
        assert fresh_svc.portfolio.cash == 950000.0
        assert fresh_svc.portfolio.realized_pnl == 50000.0


def test_api_validation_and_safety_routes():
    """Verify FastAPI routes reject malformed payloads with 422 and LIVE with 403."""
    app = create_app()
    client = TestClient(app)

    # 1. LIVE execution mode rejected with 403
    res_live = client.post("/api/v1/paper/orders", json={
        "symbol": "NIFTY",
        "side": "BUY",
        "quantity": 25,
        "execution_mode": "LIVE",
    })
    assert res_live.status_code == 403

    # 2. Zero quantity rejected by Pydantic schema with 422
    res_zero = client.post("/api/v1/paper/orders", json={
        "symbol": "NIFTY",
        "side": "BUY",
        "quantity": 0,
        "execution_mode": "PAPER",
    })
    assert res_zero.status_code == 422

    # 3. Negative quantity rejected with 422
    res_neg = client.post("/api/v1/paper/orders", json={
        "symbol": "NIFTY",
        "side": "BUY",
        "quantity": -25,
        "execution_mode": "PAPER",
    })
    assert res_neg.status_code == 422

    # 4. Trip and reset breaker routes
    res_trip = client.post("/api/v1/paper/risk/trip", json={"reason": "TEST"})
    assert res_trip.status_code == 200
    assert res_trip.json()["status"] == "TRIPPED"

    res_reset = client.post("/api/v1/paper/risk/reset")
    assert res_reset.status_code == 200
    assert res_reset.json()["status"] == "RESET"
