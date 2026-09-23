"""
Tests for Phase 9 Executable Quote Validator & Price Separation.
"""

import pytest

from src.data_infrastructure.executable_validator import ExecutableQuoteValidator
from src.data_infrastructure.models import DataStatus


def test_valid_market_buy_approved():
    res = ExecutableQuoteValidator.validate_for_execution(
        side="BUY",
        bid=22000.0,
        ask=22005.0,
        ltp=22002.5,
        quote_age_seconds=5.0,
        data_status=DataStatus.VERIFIED_DELAYED,
        is_market_open=True,
    )
    assert res.is_executable is True
    assert res.executable_price == 22005.0  # Buy fills against Ask
    assert res.valuation_mark == 22002.5


def test_valid_market_sell_approved():
    res = ExecutableQuoteValidator.validate_for_execution(
        side="SELL",
        bid=22000.0,
        ask=22005.0,
        ltp=22002.5,
        quote_age_seconds=5.0,
        data_status=DataStatus.VERIFIED_REAL_TIME,
        is_market_open=True,
    )
    assert res.is_executable is True
    assert res.executable_price == 22000.0  # Sell fills against Bid


def test_missing_ask_for_buy_rejected_even_when_ltp_exists():
    """
    CRITICAL NON-NEGOTIABLE TEST:
    LTP available, Bid unavailable, Ask unavailable -> NO FILL / NO_ASK.
    LTP must never be used for execution!
    """
    res = ExecutableQuoteValidator.validate_for_execution(
        side="BUY",
        bid=None,
        ask=None,
        ltp=22500.0,  # LTP is present!
        quote_age_seconds=5.0,
        data_status=DataStatus.VERIFIED_DELAYED,
        is_market_open=True,
    )
    assert res.is_executable is False
    assert res.rejection_code == "NO_ASK"
    assert res.valuation_mark == 22500.0  # Allowed only as mark


def test_missing_bid_for_sell_rejected():
    res = ExecutableQuoteValidator.validate_for_execution(
        side="SELL",
        bid=None,
        ask=22010.0,
        ltp=22005.0,
        quote_age_seconds=5.0,
        data_status=DataStatus.VERIFIED_DELAYED,
        is_market_open=True,
    )
    assert res.is_executable is False
    assert res.rejection_code == "NO_BID"


def test_crossed_market_rejected():
    res = ExecutableQuoteValidator.validate_for_execution(
        side="BUY",
        bid=22050.0,  # Bid > Ask!
        ask=22000.0,
        ltp=22025.0,
        quote_age_seconds=5.0,
        data_status=DataStatus.VERIFIED_REAL_TIME,
        is_market_open=True,
    )
    assert res.is_executable is False
    assert res.rejection_code == "INVALID_SPREAD"


def test_wide_spread_rejected():
    res = ExecutableQuoteValidator.validate_for_execution(
        side="BUY",
        bid=20000.0,
        ask=22000.0,  # ~9% spread (exceeds 2.5% default)
        ltp=21000.0,
        quote_age_seconds=5.0,
        data_status=DataStatus.VERIFIED_REAL_TIME,
        is_market_open=True,
    )
    assert res.is_executable is False
    assert res.rejection_code == "INVALID_SPREAD"


def test_stale_data_rejected():
    res = ExecutableQuoteValidator.validate_for_execution(
        side="BUY",
        bid=22000.0,
        ask=22005.0,
        data_status=DataStatus.STALE,
        is_market_open=True,
    )
    assert res.is_executable is False
    assert res.rejection_code == "STALE_QUOTE"


def test_market_closed_rejected():
    res = ExecutableQuoteValidator.validate_for_execution(
        side="BUY",
        bid=22000.0,
        ask=22005.0,
        data_status=DataStatus.VERIFIED_REAL_TIME,
        is_market_open=False,
    )
    assert res.is_executable is False
    assert res.rejection_code == "MARKET_CLOSED"


def test_quote_too_old_rejected():
    res = ExecutableQuoteValidator.validate_for_execution(
        side="BUY",
        bid=22000.0,
        ask=22005.0,
        quote_age_seconds=120.0,  # 2 minutes old (exceeds 60s)
        data_status=DataStatus.VERIFIED_DELAYED,
        is_market_open=True,
    )
    assert res.is_executable is False
    assert res.rejection_code == "QUOTE_TOO_OLD"
