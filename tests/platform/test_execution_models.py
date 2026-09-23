"""
Test Modular Execution and Cost Models.
"""

import pytest
from src.platform.execution_models.cost_models import (
    LTPOnlyModel,
    EODSettlementModel,
    EstimatedSlippageModel,
    HistoricalBidAskModel,
    OrderBookModel,
    get_execution_model,
)


def test_ltp_and_eod_models():
    ltp = LTPOnlyModel()
    fill = ltp.compute_fill("BUY", 100.0, 100)
    assert fill.filled is True
    assert fill.fill_price == 100.0
    assert "NO_LIQUIDITY" in fill.evidence_level

    eod = EODSettlementModel()
    fill_eod = eod.compute_fill("SELL", 200.0, 50)
    assert fill_eod.filled is True
    assert fill_eod.fill_price == 200.0


def test_estimated_slippage_model():
    model = EstimatedSlippageModel(base_slippage_bps=10.0, statutory_costs_bps=5.0)
    fill_buy = model.compute_fill("BUY", 1000.0, 10)
    assert fill_buy.fill_price > 1000.0
    assert fill_buy.total_friction_bps == 15.0

    fill_sell = model.compute_fill("SELL", 1000.0, 10)
    assert fill_sell.fill_price < 1000.0


def test_historical_bid_ask_model():
    model = HistoricalBidAskModel()
    # Missing market data -> Blocked
    fill_none = model.compute_fill("BUY", 100.0, 10, None)
    assert fill_none.filled is False
    assert "BLOCKED" in fill_none.status

    # Invalid quote (Ask < Bid) -> Blocked
    fill_inv = model.compute_fill("BUY", 100.0, 10, {"bid": 105.0, "ask": 100.0})
    assert fill_inv.filled is False
    assert "INVALID_BID_ASK" in fill_inv.status

    # Valid paired quote -> Filled
    fill_valid = model.compute_fill("BUY", 100.0, 10, {"bid": 99.5, "ask": 100.5})
    assert fill_valid.filled is True
    assert fill_valid.fill_price == 100.5


def test_order_book_model():
    model = OrderBookModel()
    # Missing depth -> Blocked
    fill_none = model.compute_fill("BUY", 100.0, 10, None)
    assert fill_none.filled is False

    # Valid depth -> Filled
    market_data = {
        "order_depth": {
            "asks": [{"price": 101.0, "qty": 50}],
            "bids": [{"price": 99.0, "qty": 50}],
        }
    }
    fill_depth = model.compute_fill("BUY", 100.0, 10, market_data)
    assert fill_depth.filled is True
    assert fill_depth.fill_price == 101.0
