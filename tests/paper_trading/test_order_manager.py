"""
Tests for PaperOrderManager in Phase 8.
"""

from datetime import datetime, timezone
import pytest

from src.paper_trading.models import (
    PaperFill,
    PaperFillSource,
    PaperOrder,
    PaperOrderExpiry,
    PaperOrderSide,
    PaperOrderStatus,
    PaperOrderType,
    RiskCheckResult,
)
from src.paper_trading.order_manager import PaperOrderManager


@pytest.fixture
def order_manager():
    return PaperOrderManager()


def test_submit_market_order(order_manager):
    """Submitting a valid market order moves it to PENDING."""
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=50,
    )
    submitted, risk = order_manager.submit_order(order)
    assert submitted.status == PaperOrderStatus.PENDING
    assert order_manager.get_order(order.order_id) is not None


def test_submit_limit_order(order_manager):
    """Submitting a valid limit order moves it to OPEN."""
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.LIMIT,
        quantity=50,
        limit_price=22000.0,
    )
    submitted, risk = order_manager.submit_order(order)
    assert submitted.status == PaperOrderStatus.OPEN


def test_reject_invalid_quantity(order_manager):
    """Quantity <= 0 is immediately rejected."""
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=0,
    )
    submitted, _ = order_manager.submit_order(order)
    assert submitted.status == PaperOrderStatus.REJECTED
    assert submitted.rejection_reason == "INVALID_QUANTITY"


def test_reject_missing_limit_price(order_manager):
    """Limit order without limit price is rejected."""
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.LIMIT,
        quantity=50,
        limit_price=None,
    )
    submitted, _ = order_manager.submit_order(order)
    assert submitted.status == PaperOrderStatus.REJECTED
    assert submitted.rejection_reason == "MISSING_LIMIT_PRICE"


def test_risk_check_rejection(order_manager):
    """Risk check failure rejects order with reason."""
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=500,
    )
    def failing_risk(o):
        return RiskCheckResult(
            is_approved=False,
            rejection_reasons=["MAX_POSITION_SIZE_EXCEEDED"],
        )

    submitted, risk = order_manager.submit_order(order, risk_check_fn=failing_risk)
    assert submitted.status == PaperOrderStatus.REJECTED
    assert "MAX_POSITION_SIZE_EXCEEDED" in submitted.rejection_reason


def test_cancel_order(order_manager):
    """Cancelling a pending order moves it to CANCELLED."""
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.LIMIT,
        quantity=50,
        limit_price=21500.0,
    )
    order_manager.submit_order(order)
    cancelled = order_manager.cancel_order(order.order_id)
    assert cancelled.status == PaperOrderStatus.CANCELLED


def test_apply_fill(order_manager):
    """Applying a fill updates quantity, average price, and status to FILLED."""
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=50,
    )
    order_manager.submit_order(order)

    now = datetime.now(timezone.utc)
    fill = PaperFill(
        order_id=order.order_id,
        symbol="NIFTY",
        fill_quantity=50,
        fill_price=22010.0,
        fill_timestamp=now,
        provider_timestamp=now,
        received_timestamp=now,
        execution_timestamp=now,
        source_provider="YFINANCE",
        price_source=PaperFillSource.PROVIDER_ASK_WITH_SLIPPAGE,
        price_source_description="Ask fill",
        data_status_at_fill="DELAYED",
        slippage_applied=1.5,
        transaction_costs=25.0,
        quote_age_seconds=1.0,
    )

    updated = order_manager.apply_fill(order.order_id, fill)
    assert updated.status == PaperOrderStatus.FILLED
    assert updated.filled_quantity == 50
    assert updated.average_fill_price == 22010.0


def test_expire_day_orders(order_manager):
    """expire_day_orders expires all open DAY orders."""
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.LIMIT,
        quantity=50,
        limit_price=21000.0,
        expiry_type=PaperOrderExpiry.DAY,
    )
    order_manager.submit_order(order)
    expired = order_manager.expire_day_orders()
    assert len(expired) == 1
    assert expired[0].status == PaperOrderStatus.EXPIRED
