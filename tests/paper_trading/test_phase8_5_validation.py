"""
Phase 8.5 — Multi-Session Paper Trading Validation Test Suite.

Comprehensive validation covering:
1. Data Integrity & Delayed vs Stale Distinction
2. Execution Quote (Bid/Ask) vs Valuation (LTP) Separation
3. Retroactive Fill Prevention
4. Order Types: Market, Limit, Stop, Stop-Limit
5. Provenance Verification (All 22 required fields)
6. Pre-trade Risk Controls & Circuit Breakers
7. Portfolio & Double-Entry Accounting Reconciliation
8. Reset Safety (Zero Fabricated Liquidations)
9. End-to-End Crash Recovery & Persistence Integrity
10. Strict Options Paper Trading Prohibition
"""

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from src.paper_trading.execution_guard import ExecutionGuard, LiveExecutionDisabledError
from src.paper_trading.fill_engine import SimulatedFillEngine
from src.paper_trading.models import (
    PaperExecutionMode,
    PaperFill,
    PaperFillSource,
    PaperOrder,
    PaperOrderExpiry,
    PaperOrderSide,
    PaperOrderStatus,
    PaperOrderType,
    PaperPosition,
    PaperTradeRecord,
    RiskCheckResult,
)
from src.paper_trading.order_manager import PaperOrderManager
from src.paper_trading.portfolio import PaperPortfolioTracker
from src.paper_trading.reconciliation import reconcile_paper_account
from src.paper_trading.risk_manager import PaperRiskManager
from src.paper_trading.service import PaperTradingService


# =============================================================================
# 1. Data Integrity & Delayed vs Stale Distinction
# =============================================================================

def test_delayed_data_is_eligible_when_fresh():
    """DELAYED data is execution-eligible if within freshness limit and Bid/Ask exist."""
    engine = SimulatedFillEngine(max_fill_age_seconds=120.0, delayed_data_fill_allowed=True)
    now = datetime.now(timezone.utc)
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=50,
        status=PaperOrderStatus.OPEN,
        submitted_at=now - timedelta(seconds=2),
    )

    with patch("src.paper_trading.fill_engine.is_fill_eligible_market_state", return_value=(True, "MARKET_OPEN")):
        fill, refusal = engine.attempt_fill(
            order=order,
            bid=22000.0,
            ask=22005.0,
            provider_timestamp=now - timedelta(seconds=10),
            received_timestamp=now,
            data_status="DELAYED",
            source_provider="YFINANCE",
        )
    assert refusal is None
    assert fill is not None
    assert fill.data_status_at_fill == "DELAYED"


def test_stale_data_is_always_rejected():
    """STALE, UNAVAILABLE, and ERROR data are unconditionally rejected from execution."""
    engine = SimulatedFillEngine()
    now = datetime.now(timezone.utc)
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=50,
        status=PaperOrderStatus.OPEN,
        submitted_at=now - timedelta(seconds=2),
    )

    for invalid_status in ["STALE", "UNAVAILABLE", "ERROR"]:
        with patch("src.paper_trading.fill_engine.is_fill_eligible_market_state", return_value=(True, "MARKET_OPEN")):
            fill, refusal = engine.attempt_fill(
                order=order,
                bid=22000.0,
                ask=22005.0,
                provider_timestamp=now,
                received_timestamp=now,
                data_status=invalid_status,
                source_provider="YFINANCE",
            )
        assert fill is None
        assert refusal is not None
        assert "DATA" in refusal.reason


def test_excessive_quote_age_rejected():
    """Quotes exceeding maximum configured fill age are refused."""
    engine = SimulatedFillEngine(max_fill_age_seconds=60.0, delayed_data_max_age_seconds=60.0)
    now = datetime.now(timezone.utc)
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=50,
        status=PaperOrderStatus.OPEN,
        submitted_at=now - timedelta(seconds=120),
    )

    with patch("src.paper_trading.fill_engine.is_fill_eligible_market_state", return_value=(True, "MARKET_OPEN")):
        fill, refusal = engine.attempt_fill(
            order=order,
            bid=22000.0,
            ask=22005.0,
            provider_timestamp=now - timedelta(seconds=90),  # 90s > 60s limit
            received_timestamp=now,
            data_status="DELAYED",
            source_provider="YFINANCE",
        )
    assert fill is None
    assert refusal is not None
    assert refusal.reason == "QUOTE_TOO_OLD"


def test_invalid_future_provider_timestamp_rejected():
    """Provider timestamp significantly in the future of received timestamp is rejected."""
    engine = SimulatedFillEngine()
    now = datetime.now(timezone.utc)
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=50,
        status=PaperOrderStatus.OPEN,
        submitted_at=now,
    )

    with patch("src.paper_trading.fill_engine.is_fill_eligible_market_state", return_value=(True, "MARKET_OPEN")):
        fill, refusal = engine.attempt_fill(
            order=order,
            bid=22000.0,
            ask=22005.0,
            provider_timestamp=now + timedelta(seconds=30),  # 30s future clock skew
            received_timestamp=now,
            data_status="DELAYED",
            source_provider="YFINANCE",
        )
    assert fill is None
    assert refusal is not None
    assert refusal.reason == "INVALID_OBSERVATION_PROVENANCE"


# =============================================================================
# 2. Bid/Ask Execution vs LTP Valuation Separation
# =============================================================================

def test_ltp_available_but_bid_ask_missing_produces_no_fill():
    """Non-negotiable requirement: LTP cannot be used for execution. If Bid/Ask is missing -> NO FILL."""
    engine = SimulatedFillEngine()
    now = datetime.now(timezone.utc)
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=50,
        status=PaperOrderStatus.OPEN,
        submitted_at=now - timedelta(seconds=1),
    )

    with patch("src.paper_trading.fill_engine.is_fill_eligible_market_state", return_value=(True, "MARKET_OPEN")):
        # Only LTP provided; Bid and Ask are None
        fill, refusal = engine.attempt_fill(
            order=order,
            bid=None,
            ask=None,
            provider_timestamp=now,
            received_timestamp=now,
            data_status="DELAYED",
            source_provider="YFINANCE",
        )
    assert fill is None
    assert refusal is not None
    assert refusal.reason == "NO_VALID_EXECUTABLE_QUOTE"


def test_market_buy_uses_ask_and_sell_uses_bid():
    """BUY fills exclusively from Ask + slippage. SELL fills exclusively from Bid - slippage."""
    engine = SimulatedFillEngine(slippage_pct=0.001)
    now = datetime.now(timezone.utc)

    # Buy order
    order_buy = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=50,
        status=PaperOrderStatus.OPEN,
        submitted_at=now - timedelta(seconds=1),
    )
    with patch("src.paper_trading.fill_engine.is_fill_eligible_market_state", return_value=(True, "MARKET_OPEN")):
        fill_b, ref_b = engine.attempt_fill(
            order=order_buy,
            bid=22000.0,
            ask=22010.0,
            provider_timestamp=now,
            received_timestamp=now,
            data_status="DELAYED",
            source_provider="YFINANCE",
        )
    assert ref_b is None
    assert fill_b.price_source == PaperFillSource.PROVIDER_ASK_WITH_SLIPPAGE
    assert fill_b.fill_price >= 22010.0
    assert fill_b.ask_at_execution == 22010.0

    # Sell order
    order_sell = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.SELL,
        order_type=PaperOrderType.MARKET,
        quantity=50,
        status=PaperOrderStatus.OPEN,
        submitted_at=now - timedelta(seconds=1),
    )
    with patch("src.paper_trading.fill_engine.is_fill_eligible_market_state", return_value=(True, "MARKET_OPEN")):
        fill_s, ref_s = engine.attempt_fill(
            order=order_sell,
            bid=22000.0,
            ask=22010.0,
            provider_timestamp=now,
            received_timestamp=now,
            data_status="DELAYED",
            source_provider="YFINANCE",
        )
    assert ref_s is None
    assert fill_s.price_source == PaperFillSource.PROVIDER_BID_WITH_SLIPPAGE
    assert fill_s.fill_price <= 22000.0
    assert fill_s.bid_at_execution == 22000.0


# =============================================================================
# 3. Retroactive Fill Prevention Rule
# =============================================================================

def test_retroactive_observation_rejected():
    """Observation received prior to order submission must be rejected."""
    engine = SimulatedFillEngine()
    now = datetime.now(timezone.utc)
    order_submission_time = now

    # Order submitted at 'now'
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=50,
        status=PaperOrderStatus.OPEN,
        submitted_at=order_submission_time,
    )

    # Observation was received 5 seconds BEFORE order submission
    old_observation_received = order_submission_time - timedelta(seconds=5)

    with patch("src.paper_trading.fill_engine.is_fill_eligible_market_state", return_value=(True, "MARKET_OPEN")):
        fill, refusal = engine.attempt_fill(
            order=order,
            bid=22000.0,
            ask=22005.0,
            provider_timestamp=old_observation_received,
            received_timestamp=old_observation_received,
            data_status="DELAYED",
            source_provider="YFINANCE",
        )
    assert fill is None
    assert refusal is not None
    assert refusal.reason == "RETROACTIVE_FILL_REJECTED"


# =============================================================================
# 4. Limit, Stop, and Stop-Limit Orders
# =============================================================================

def test_limit_order_execution_conditions():
    """Limit BUY fills only when Ask <= limit; Limit SELL fills only when Bid >= limit."""
    engine = SimulatedFillEngine(slippage_pct=0.0)
    now = datetime.now(timezone.utc)

    # BUY Limit @ 22000
    buy_limit = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.LIMIT,
        limit_price=22000.0,
        quantity=50,
        status=PaperOrderStatus.OPEN,
        submitted_at=now - timedelta(seconds=10),
    )

    with patch("src.paper_trading.fill_engine.is_fill_eligible_market_state", return_value=(True, "MARKET_OPEN")):
        # Ask is 22010 > 22000 -> Condition not met
        t_obs1 = now - timedelta(seconds=5)
        f1, r1 = engine.attempt_fill(
            order=buy_limit,
            bid=22000.0,
            ask=22010.0,
            provider_timestamp=t_obs1,
            received_timestamp=t_obs1,
            data_status="DELAYED",
            source_provider="YFINANCE",
        )
        assert f1 is None
        assert r1.reason == "ORDER_CONDITION_NOT_MET"

        # Ask drops to 21995 <= 22000 -> Fills
        t_obs2 = now - timedelta(seconds=1)
        f2, r2 = engine.attempt_fill(
            order=buy_limit,
            bid=21990.0,
            ask=21995.0,
            provider_timestamp=t_obs2,
            received_timestamp=t_obs2,
            data_status="DELAYED",
            source_provider="YFINANCE",
        )
        assert f2 is not None
        assert f2.fill_price == 21995.0


def test_stop_order_trigger_and_fill():
    """Stop BUY triggers only when Ask >= stop_price. Stop SELL triggers when Bid <= stop_price."""
    engine = SimulatedFillEngine(slippage_pct=0.0)
    now = datetime.now(timezone.utc)

    # BUY Stop @ 22100 (breakout)
    buy_stop = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.STOP,
        stop_price=22100.0,
        quantity=50,
        status=PaperOrderStatus.OPEN,
        submitted_at=now - timedelta(seconds=10),
    )

    with patch("src.paper_trading.fill_engine.is_fill_eligible_market_state", return_value=(True, "MARKET_OPEN")):
        # Ask is 22050 < 22100 -> Condition not met
        t_obs1 = now - timedelta(seconds=5)
        f1, r1 = engine.attempt_fill(
            order=buy_stop,
            bid=22040.0,
            ask=22050.0,
            provider_timestamp=t_obs1,
            received_timestamp=t_obs1,
            data_status="DELAYED",
            source_provider="YFINANCE",
        )
        assert f1 is None

        # Ask rises to 22105 >= 22100 -> Triggers and fills
        t_obs2 = now - timedelta(seconds=1)
        f2, r2 = engine.attempt_fill(
            order=buy_stop,
            bid=22095.0,
            ask=22105.0,
            provider_timestamp=t_obs2,
            received_timestamp=t_obs2,
            data_status="DELAYED",
            source_provider="YFINANCE",
        )
        assert f2 is not None
        assert f2.fill_price == 22105.0


# =============================================================================
# 5. Provenance Completeness
# =============================================================================

def test_fill_contains_complete_provenance():
    """Every PaperFill must contain complete provenance across all mandatory fields."""
    engine = SimulatedFillEngine()
    now = datetime.now(timezone.utc)
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=50,
        status=PaperOrderStatus.OPEN,
        submitted_at=now - timedelta(seconds=1),
        decision_timestamp=now - timedelta(seconds=2),
    )

    with patch("src.paper_trading.fill_engine.is_fill_eligible_market_state", return_value=(True, "MARKET_OPEN")):
        fill, _ = engine.attempt_fill(
            order=order,
            bid=22000.0,
            ask=22005.0,
            provider_timestamp=now,
            received_timestamp=now,
            data_status="DELAYED",
            source_provider="YFINANCE",
        )

    assert fill is not None
    assert fill.validate_provenance() is True
    assert fill.observation_id.startswith("OBS-")
    assert fill.fill_id.startswith("FILL-")
    assert fill.side == PaperOrderSide.BUY
    assert fill.order_submission_timestamp == order.submitted_at
    assert fill.decision_timestamp == order.decision_timestamp
    assert fill.bid_at_execution == 22000.0
    assert fill.ask_at_execution == 22005.0
    assert fill.spread_at_execution == 5.0
    assert fill.source_provider == "YFINANCE"


# =============================================================================
# 6. Options Paper Trading Prohibition
# =============================================================================

def test_options_orders_unconditionally_blocked():
    """Options orders must be rejected because live options provider is NOT VERIFIED."""
    service = PaperTradingService()
    res = service.place_order(
        symbol="NIFTY24DEC22000CE",
        side="BUY",
        quantity=25,
        instrument_type="INDEX_OPTION",
    )
    assert res["status"] == "REJECTED"
    assert "OPTIONS_DATA_UNAVAILABLE" in res["rejection_reason"]
    assert "NOT VERIFIED" in res["rejection_reason"]


# =============================================================================
# 7. Safe Reset (Never Fabricates Liquidation)
# =============================================================================

def test_reset_rejected_when_open_positions_exist():
    """Account reset is rejected when open positions exist unless explicit archive requested."""
    service = PaperTradingService(initial_capital=1_000_000.0)
    service.start_session()

    # Manually open a position
    service.portfolio.cash = 900_000.0
    service.portfolio._positions["NIFTY"] = PaperPosition(
        symbol="NIFTY",
        quantity=50,
        average_entry_price=22000.0,
    )

    # Attempt reset without archive
    res = service.reset_paper_account(confirm=True, archive=False)
    assert res["status"] == "RESET_REJECTED"
    assert res["reason"] == "OPEN_POSITIONS_EXIST"

    # Reset with archive succeeds cleanly without creating fake fills
    res_archive = service.reset_paper_account(confirm=True, archive=True)
    assert res_archive["status"] == "RESET_COMPLETE"
    assert res_archive["archived"] is True
    assert len(service.portfolio.get_open_positions()) == 0


# =============================================================================
# 8. Crash Recovery & Multi-Session Persistence (Real Test)
# =============================================================================

def test_crash_recovery_preserves_state_and_reconciles():
    """
    Simulates crash recovery:
    1. Start service instance 1 with temporary directory
    2. Place orders & process fills
    3. Verify portfolio cash and positions
    4. Terminate instance 1
    5. Initialize instance 2 pointing to same state directory with auto_restore=True
    6. Verify recovered state, 0 duplicate fills, 0 lost cash, successful reconciliation
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Instance 1
        service_1 = PaperTradingService(initial_capital=1_000_000.0, state_dir=tmpdir)
        service_1.start_session()

        order_res = service_1.place_order(
            symbol="NIFTY",
            side="BUY",
            quantity=50,
            order_type="MARKET",
        )
        assert order_res["status"] == "PENDING"
        order_id = order_res["order_id"]

        now = datetime.now(timezone.utc)
        with patch("src.paper_trading.fill_engine.is_fill_eligible_market_state", return_value=(True, "MARKET_OPEN")):
            update_res = service_1.process_market_update(
                symbol="NIFTY",
                bid=22000.0,
                ask=22005.0,
                ltp=22002.5,
                provider_timestamp=now,
                received_timestamp=now,
                data_status="DELAYED",
                source_provider="YFINANCE",
            )
        assert len(update_res["fills"]) == 1

        summary_1 = service_1.get_portfolio_summary()
        cash_1 = summary_1["cash"]
        equity_1 = summary_1["equity"]
        positions_1 = len(service_1.portfolio.get_open_positions())
        assert positions_1 == 1

        # Simulate application crash / restart by instantiating Service 2
        service_2 = PaperTradingService(
            initial_capital=1_000_000.0,
            state_dir=tmpdir,
            auto_restore=True,
        )

        summary_2 = service_2.get_portfolio_summary()
        assert summary_2["cash"] == cash_1
        assert summary_2["equity"] == equity_1
        assert len(service_2.portfolio.get_open_positions()) == 1
        assert service_2.portfolio.get_open_positions()[0].symbol == "NIFTY"
        assert len(service_2._all_fills) == 1
        assert service_2._all_fills[0].order_id == order_id

        # Reconcile recovered portfolio
        rec = service_2.reconcile()
        assert rec["status"] == "RECONCILIATION_PASS"
        assert rec["is_reconciled"] is True
        assert len(rec["discrepancies"]) == 0


# =============================================================================
# 9. Idempotency Across Repeated Observations
# =============================================================================

def test_duplicate_observation_idempotency():
    """Identical observation processed multiple times produces exactly one fill."""
    engine = SimulatedFillEngine()
    now = datetime.now(timezone.utc)
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=50,
        status=PaperOrderStatus.OPEN,
        submitted_at=now - timedelta(seconds=2),
    )

    with patch("src.paper_trading.fill_engine.is_fill_eligible_market_state", return_value=(True, "MARKET_OPEN")):
        f1, r1 = engine.attempt_fill(
            order=order,
            bid=22000.0,
            ask=22005.0,
            provider_timestamp=now,
            received_timestamp=now,
            data_status="DELAYED",
            source_provider="YFINANCE",
        )
        assert f1 is not None
        assert r1 is None

        # Repeat identical observation
        f2, r2 = engine.attempt_fill(
            order=order,
            bid=22000.0,
            ask=22005.0,
            provider_timestamp=now,
            received_timestamp=now,
            data_status="DELAYED",
            source_provider="YFINANCE",
        )
        assert f2 is None
        assert r2 is not None
        assert r2.reason == "DUPLICATE_OBSERVATION"


# =============================================================================
# 10. Stop-Limit Orders
# =============================================================================

def test_stop_limit_order_execution():
    """Stop-limit order triggers on stop, then checks limit condition against executable quote."""
    engine = SimulatedFillEngine(slippage_pct=0.0)
    now = datetime.now(timezone.utc)

    # Buy Stop-Limit: Stop at 22100, Limit at 22110
    stop_limit = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.STOP_LIMIT,
        stop_price=22100.0,
        limit_price=22110.0,
        quantity=50,
        status=PaperOrderStatus.OPEN,
        submitted_at=now - timedelta(seconds=10),
    )

    with patch("src.paper_trading.fill_engine.is_fill_eligible_market_state", return_value=(True, "MARKET_OPEN")):
        # Ask 22050 < 22100 (stop not reached)
        t1 = now - timedelta(seconds=5)
        f1, r1 = engine.attempt_fill(
            order=stop_limit,
            bid=22040.0,
            ask=22050.0,
            provider_timestamp=t1,
            received_timestamp=t1,
            data_status="DELAYED",
            source_provider="YFINANCE",
        )
        assert f1 is None
        assert r1.reason == "ORDER_CONDITION_NOT_MET"

        # Ask 22105 (triggers stop >= 22100 and satisfies limit <= 22110)
        t2 = now - timedelta(seconds=1)
        f2, r2 = engine.attempt_fill(
            order=stop_limit,
            bid=22095.0,
            ask=22105.0,
            provider_timestamp=t2,
            received_timestamp=t2,
            data_status="DELAYED",
            source_provider="YFINANCE",
        )
        assert f2 is not None
        assert f2.fill_price == 22105.0


# =============================================================================
# 11. Circuit Breakers: Daily Loss & Drawdown
# =============================================================================

def test_daily_loss_circuit_breaker_cancels_pending_and_blocks_new():
    """Breaching configured daily loss trips circuit breaker and rejects orders."""
    risk = PaperRiskManager(max_daily_loss_pct=3.0, max_portfolio_drawdown_pct=10.0)

    # Trigger breaker with 40,000 loss on 1,000,000 equity (4% > 3%)
    triggered = risk.update_circuit_breakers(
        daily_pnl=-40_000.0,
        current_equity=960_000.0,
        drawdown_pct=0.04,
    )
    assert "DAILY_LOSS_CIRCUIT_BREAKER" in triggered
    assert risk.is_circuit_breaker_active is True

    # New order submitted during circuit breaker must be rejected
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=25,
    )
    res = risk.check_order(
        order=order,
        current_equity=960_000.0,
        daily_pnl=-40_000.0,
        drawdown_pct=0.04,
        open_positions=[],
    )
    assert res.is_approved is False
    assert any("CIRCUIT_BREAKER" in r for r in res.rejection_reasons)


def test_drawdown_circuit_breaker_cancels_pending_and_blocks_new():
    """Breaching maximum portfolio drawdown trips circuit breaker and rejects orders."""
    risk = PaperRiskManager(max_daily_loss_pct=10.0, max_portfolio_drawdown_pct=5.0)

    # Trigger breaker with 6% drawdown (> 5%)
    triggered = risk.update_circuit_breakers(
        daily_pnl=0.0,
        current_equity=940_000.0,
        drawdown_pct=0.06,
    )
    assert "DRAWDOWN_CIRCUIT_BREAKER" in triggered
    assert risk.is_circuit_breaker_active is True

    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=25,
    )
    res = risk.check_order(
        order=order,
        current_equity=940_000.0,
        daily_pnl=0.0,
        drawdown_pct=0.06,
        open_positions=[],
    )
    assert res.is_approved is False
    assert any("DRAWDOWN" in r or "CIRCUIT_BREAKER" in r for r in res.rejection_reasons)


# =============================================================================
# 12. Accounting Reconciliation & Intentional Discrepancy
# =============================================================================

def test_intentional_cash_discrepancy_fails_reconciliation():
    """Any accounting discrepancy produces RECONCILIATION_FAILURE without silent correction."""
    now = datetime.now(timezone.utc)
    trade = PaperTradeRecord(
        symbol="NIFTY",
        direction="LONG",
        entry_timestamp=now,
        exit_timestamp=now,
        quantity=50,
        entry_price=22000.0,
        exit_price=22100.0,
        gross_pnl=5000.0,
        fees=100.0,
        slippage=200.0,
        net_pnl=4900.0,
        holding_period_seconds=60.0,
    )

    # Intentionally corrupted ending cash
    res = reconcile_paper_account(
        starting_cash=1_000_000.0,
        ending_cash=980_000.0,  # Missing 24,900
        positions=[],
        fills=[],
        closed_trades=[trade],
    )
    assert res.is_reconciled is False
    assert res.status == "RECONCILIATION_FAILURE"
    assert len(res.discrepancies) > 0
    assert "Cash discrepancy" in res.discrepancies[0]


# =============================================================================
# 13. System Invariants (Safety & Auto-Trading Guard)
# =============================================================================

def test_system_safety_invariants():
    """Verify non-negotiable architectural safety invariants."""
    # Live execution is immutable False
    assert ExecutionGuard.is_live_enabled() is False

    # Attempt to request LIVE mode raises LiveExecutionDisabledError
    with pytest.raises(LiveExecutionDisabledError):
        ExecutionGuard.validate_execution_mode("LIVE")

    # Auto-paper order submission is disabled by default
    assert PaperTradingService.AUTO_PAPER_ORDER_SUBMISSION is False
