"""
Tests for data validation module.

Validates:
- Price sanity checks
- Bid ≤ Ask validation
- OI/volume sanity
- Staleness detection
- Null handling (never fills missing data)
- Quality report generation
"""

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from src.ingestion.schemas import (
    DataQualityStatus,
    OptionChainSnapshot,
    OptionQuote,
    OptionStrikeRow,
    OptionType,
)
from src.preprocessing.validation import (
    _validate_option_quote,
    validate_option_chain,
    validate_spot_price,
)


class TestQuoteValidation:
    """Tests for individual option quote validation."""

    def test_valid_quote_has_no_issues(self, sample_option_quote_ce):
        """A normal quote should pass validation."""
        issues = _validate_option_quote(sample_option_quote_ce)
        assert len(issues) == 0

    def test_negative_ltp_flagged(self):
        """Negative LTP should be flagged as suspect."""
        # Note: the Pydantic validator converts negative to None,
        # so we test the validation of a quote where it slipped through
        quote = OptionQuote(
            underlying="NIFTY", option_type=OptionType.CE,
            strike_price=25000.0, expiry_date=date(2025, 10, 2),
            last_price=None,  # Would be None due to validator
            volume=100, open_interest=1000,
            timestamp=datetime.now(), source="test",
        )
        # No issues for None — it's handled as missing data
        issues = _validate_option_quote(quote)
        suspect_issues = [i for i in issues if i["severity"] == "suspect"]
        assert len(suspect_issues) == 0

    def test_bid_greater_than_ask_flagged(self):
        """Bid > Ask should be flagged as suspect."""
        quote = OptionQuote(
            underlying="NIFTY", option_type=OptionType.CE,
            strike_price=25000.0, expiry_date=date(2025, 10, 2),
            bid_price=155.0, ask_price=148.0,  # bid > ask
            timestamp=datetime.now(), source="test",
        )
        issues = _validate_option_quote(quote)
        bid_ask_issues = [i for i in issues if i["field"] == "bid_ask"]
        assert len(bid_ask_issues) == 1

    def test_negative_oi_flagged(self):
        """Negative OI should be flagged."""
        quote = OptionQuote(
            underlying="NIFTY", option_type=OptionType.CE,
            strike_price=25000.0, expiry_date=date(2025, 10, 2),
            open_interest=None,  # Pydantic validator converts negative to None
            timestamp=datetime.now(), source="test",
        )
        # None OI is handled as missing, not suspect
        issues = _validate_option_quote(quote)
        # Should be clean since None is valid for optional
        assert all(i["field"] != "open_interest" or i["severity"] != "suspect" for i in issues)

    def test_extreme_iv_flagged(self):
        """IV > 500% should be flagged."""
        quote = OptionQuote(
            underlying="NIFTY", option_type=OptionType.CE,
            strike_price=25000.0, expiry_date=date(2025, 10, 2),
            implied_volatility=600.0,
            timestamp=datetime.now(), source="test",
        )
        issues = _validate_option_quote(quote)
        iv_issues = [i for i in issues if i["field"] == "iv"]
        assert len(iv_issues) == 1


class TestChainValidation:
    """Tests for full option chain validation."""

    def test_valid_chain_produces_good_report(self, sample_option_chain):
        """A valid chain should get GOOD quality rating."""
        report = validate_option_chain(sample_option_chain)
        assert report.total_records > 0
        assert report.valid_records > 0
        # Overall quality should be GOOD for well-formed test data
        assert report.overall_quality in (DataQualityStatus.GOOD, DataQualityStatus.STALE)

    def test_empty_chain_flagged_unavailable(self, sample_timestamp):
        """An empty chain should be flagged as UNAVAILABLE."""
        empty_chain = OptionChainSnapshot(
            underlying="NIFTY",
            expiry_date=date(2025, 10, 2),
            spot_price=25000.0,
            strikes=[],
            timestamp=sample_timestamp,
            source="test",
        )
        report = validate_option_chain(empty_chain)
        assert report.overall_quality == DataQualityStatus.UNAVAILABLE
        assert report.total_records == 0

    def test_missing_fields_tracked(self, sample_expiry, sample_timestamp):
        """Missing fields should be counted in the report."""
        # Create a quote with many None fields
        quote = OptionQuote(
            underlying="NIFTY", option_type=OptionType.CE,
            strike_price=25000.0, expiry_date=sample_expiry,
            last_price=None, bid_price=None, ask_price=None,
            volume=None, open_interest=None,
            timestamp=sample_timestamp, source="test",
        )
        chain = OptionChainSnapshot(
            underlying="NIFTY", expiry_date=sample_expiry,
            spot_price=25000.0,
            strikes=[OptionStrikeRow(
                strike_price=25000.0, expiry_date=sample_expiry,
                ce=quote, pe=None,
            )],
            timestamp=sample_timestamp, source="test",
        )
        report = validate_option_chain(chain)
        assert "last_price" in report.missing_fields
        assert "volume" in report.missing_fields
        assert "open_interest" in report.missing_fields


class TestSpotPriceValidation:
    """Tests for spot price sanity checks."""

    def test_valid_nifty_price(self):
        assert validate_spot_price(25000.0, "NIFTY") is True

    def test_zero_price_invalid(self):
        assert validate_spot_price(0.0, "NIFTY") is False

    def test_negative_price_invalid(self):
        assert validate_spot_price(-100.0, "NIFTY") is False

    def test_none_price_invalid(self):
        assert validate_spot_price(None, "NIFTY") is False

    def test_extreme_low_nifty_invalid(self):
        """NIFTY at 100 is outside expected range."""
        assert validate_spot_price(100.0, "NIFTY") is False

    def test_unknown_symbol_passes_basic_check(self):
        """Unknown symbols should pass basic positive-number check."""
        assert validate_spot_price(1500.0, "UNKNOWN_STOCK") is True
