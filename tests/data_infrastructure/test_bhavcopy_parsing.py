"""
Tests for Phase 9 NSE Bhavcopy CSV Parsing & Coverage Auditing.
"""

from datetime import date
import pytest

from src.data_infrastructure.providers.bhavcopy_provider import NSEBhavcopyHistoricalProvider


def test_parse_bhavcopy_csv_content():
    # Sample genuine NSE FO Bhavcopy CSV snippet
    csv_text = """INSTRUMENT,SYMBOL,EXPIRY_DT,STRIKE_PR,OPTION_TYP,OPEN,HIGH,LOW,CLOSE,SETTLE_PR,CONTRACTS,VAL_INLAKH,OPEN_INT,CHG_IN_OI,TIMESTAMP
OPTIDX,NIFTY,27-Mar-2025,23000,CE,150.0,180.0,140.0,175.0,175.0,2500,1093.75,450000,12500,27-Feb-2025
OPTIDX,NIFTY,27-Mar-2025,23000,PE,210.0,230.0,190.0,205.0,205.0,3100,1588.75,520000,-8500,27-Feb-2025
"""
    provider = NSEBhavcopyHistoricalProvider()
    records = provider.parse_bhavcopy_csv(csv_text)

    assert len(records) == 2
    r_ce = records[0]
    assert r_ce["symbol"] == "NIFTY"
    assert r_ce["option_type"] == "CE"
    assert r_ce["strike_price"] == 23000.0
    assert r_ce["expiry_date"] == date(2025, 3, 27)
    assert r_ce["last_price"] == 175.0
    # Crucial test: Bhavcopy settlement records do NOT contain Bid/Ask -> must be None!
    assert r_ce["bid_price"] is None
    assert r_ce["ask_price"] is None
    assert r_ce["open_interest"] == 450000
    assert r_ce["change_in_oi"] == 12500


def test_bhavcopy_audit_quality_reports_zero_bid_ask():
    provider = NSEBhavcopyHistoricalProvider()
    audit = provider.audit_dataset_quality("NON_EXISTENT_SYMBOL", date(2025, 1, 1), date(2025, 1, 2))
    assert audit["bid_ask_coverage_pct"] == 0.0
    assert audit["is_suitable_for_execution"] is False
