"""
Shared test fixtures and mock data.

ALL mock/fake data is STRICTLY confined to this test module.
None of it leaks into production code.
"""

from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path

import pytest

# Ensure project root is on path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.ingestion.schemas import (
    DataQualityStatus,
    Exchange,
    InstrumentType,
    Moneyness,
    OptionChainSnapshot,
    OptionContract,
    OptionQuote,
    OptionStrikeRow,
    OptionType,
)


@pytest.fixture
def sample_spot_price() -> float:
    """Sample NIFTY spot price for testing."""
    return 25000.0


@pytest.fixture
def sample_expiry() -> date:
    """Sample expiry date for testing."""
    return date(2025, 10, 2)


@pytest.fixture
def sample_timestamp() -> datetime:
    """Sample timestamp for testing."""
    return datetime(2025, 9, 25, 12, 0, 0)


@pytest.fixture
def sample_option_quote_ce(sample_timestamp, sample_expiry) -> OptionQuote:
    """Sample CE option quote — test fixture ONLY."""
    return OptionQuote(
        underlying="NIFTY",
        option_type=OptionType.CE,
        strike_price=25000.0,
        expiry_date=sample_expiry,
        last_price=150.0,
        bid_price=148.0,
        ask_price=152.0,
        volume=50000,
        open_interest=1000000,
        change_in_oi=50000,
        implied_volatility=15.5,
        bid_ask_spread=4.0,
        bid_ask_spread_pct=2.67,
        volume_oi_ratio=0.05,
        timestamp=sample_timestamp,
        source="test_fixture",
        data_quality=DataQualityStatus.GOOD,
    )


@pytest.fixture
def sample_option_quote_pe(sample_timestamp, sample_expiry) -> OptionQuote:
    """Sample PE option quote — test fixture ONLY."""
    return OptionQuote(
        underlying="NIFTY",
        option_type=OptionType.PE,
        strike_price=25000.0,
        expiry_date=sample_expiry,
        last_price=140.0,
        bid_price=138.0,
        ask_price=142.0,
        volume=45000,
        open_interest=900000,
        change_in_oi=40000,
        implied_volatility=16.0,
        bid_ask_spread=4.0,
        bid_ask_spread_pct=2.86,
        volume_oi_ratio=0.05,
        timestamp=sample_timestamp,
        source="test_fixture",
        data_quality=DataQualityStatus.GOOD,
    )


@pytest.fixture
def sample_option_chain(sample_spot_price, sample_expiry, sample_timestamp) -> OptionChainSnapshot:
    """
    Sample option chain with multiple strikes — test fixture ONLY.
    Includes a mix of ITM, ATM, and OTM strikes with realistic relationships.
    """
    strikes_data = [
        # (strike, ce_ltp, ce_oi, pe_ltp, pe_oi, ce_iv, pe_iv, ce_chg_oi, pe_chg_oi)
        (24500, 510.0, 200000, 15.0, 1500000, 18.0, 14.0, 10000, 80000),
        (24600, 415.0, 300000, 20.0, 1200000, 17.5, 14.5, 15000, 60000),
        (24700, 320.0, 400000, 28.0, 1100000, 17.0, 15.0, 20000, 50000),
        (24800, 230.0, 600000, 40.0, 900000, 16.5, 15.5, 30000, 40000),
        (24900, 155.0, 800000, 60.0, 800000, 16.0, 16.0, 40000, 35000),
        (25000, 100.0, 1200000, 95.0, 1000000, 15.5, 16.2, 50000, 45000),  # ATM
        (25100, 60.0, 900000, 150.0, 700000, 15.0, 16.5, 35000, 30000),
        (25200, 35.0, 1500000, 230.0, 500000, 14.8, 17.0, 80000, 20000),
        (25300, 18.0, 1100000, 315.0, 400000, 14.5, 17.5, 60000, 15000),
        (25400, 8.0, 700000, 405.0, 300000, 14.0, 18.0, 25000, 10000),
        (25500, 3.0, 1800000, 500.0, 200000, 13.5, 18.5, 90000, 5000),
    ]

    strike_rows = []
    for strike, ce_ltp, ce_oi, pe_ltp, pe_oi, ce_iv, pe_iv, ce_chg, pe_chg in strikes_data:
        ce_quote = OptionQuote(
            underlying="NIFTY", option_type=OptionType.CE,
            strike_price=strike, expiry_date=sample_expiry,
            last_price=ce_ltp, bid_price=ce_ltp - 2, ask_price=ce_ltp + 2,
            volume=int(ce_oi * 0.05), open_interest=ce_oi,
            change_in_oi=ce_chg, implied_volatility=ce_iv,
            timestamp=sample_timestamp, source="test_fixture",
        )
        pe_quote = OptionQuote(
            underlying="NIFTY", option_type=OptionType.PE,
            strike_price=strike, expiry_date=sample_expiry,
            last_price=pe_ltp, bid_price=pe_ltp - 2, ask_price=pe_ltp + 2,
            volume=int(pe_oi * 0.04), open_interest=pe_oi,
            change_in_oi=pe_chg, implied_volatility=pe_iv,
            timestamp=sample_timestamp, source="test_fixture",
        )
        strike_rows.append(OptionStrikeRow(
            strike_price=strike,
            expiry_date=sample_expiry,
            ce=ce_quote,
            pe=pe_quote,
        ))

    total_ce_oi = sum(s[2] for s in strikes_data)
    total_pe_oi = sum(s[4] for s in strikes_data)

    return OptionChainSnapshot(
        underlying="NIFTY",
        expiry_date=sample_expiry,
        spot_price=sample_spot_price,
        strikes=strike_rows,
        total_ce_oi=total_ce_oi,
        total_pe_oi=total_pe_oi,
        atm_strike=25000.0,
        available_expiries=[sample_expiry],
        timestamp=sample_timestamp,
        source="test_fixture",
        data_quality=DataQualityStatus.GOOD,
    )


@pytest.fixture
def sample_option_contract(sample_expiry) -> OptionContract:
    """Sample option contract — test fixture ONLY."""
    return OptionContract(
        underlying="NIFTY",
        exchange=Exchange.NSE,
        instrument_type=InstrumentType.INDEX,
        option_type=OptionType.CE,
        strike_price=25000.0,
        expiry_date=sample_expiry,
        contract_symbol="NIFTY25OCT25000CE",
        lot_size=25,
    )
