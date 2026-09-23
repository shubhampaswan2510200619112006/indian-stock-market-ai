"""
Tests for Pydantic data schemas.

Validates:
- Static contract vs dynamic observation separation
- Data quality propagation
- Null handling (never fills missing data)
- Field validators
- Serialization/deserialization
"""

import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from src.ingestion.schemas import (
    DataQualityStatus,
    DataRecord,
    Exchange,
    GreeksObservation,
    ImpliedVolatilityObs,
    InstrumentType,
    Moneyness,
    OptionChainAnalysis,
    OptionChainSnapshot,
    OptionContract,
    OptionQuote,
    OptionStrikeRow,
    OptionType,
    Quote,
)


class TestOptionContract:
    """Tests for the static option contract model."""

    def test_contract_has_no_dynamic_fields(self, sample_option_contract):
        """Contract should NOT contain IV, Greeks, LTP, volume, OI."""
        contract = sample_option_contract
        # These attributes should NOT exist on OptionContract
        assert not hasattr(contract, "implied_volatility")
        assert not hasattr(contract, "delta")
        assert not hasattr(contract, "gamma")
        assert not hasattr(contract, "theta")
        assert not hasattr(contract, "vega")
        assert not hasattr(contract, "last_price")
        assert not hasattr(contract, "volume")
        assert not hasattr(contract, "open_interest")

    def test_contract_has_static_fields(self, sample_option_contract):
        """Contract should contain only static info."""
        contract = sample_option_contract
        assert contract.underlying == "NIFTY"
        assert contract.option_type == OptionType.CE
        assert contract.strike_price == 25000.0
        assert contract.expiry_date == date(2025, 10, 2)
        assert contract.lot_size == 25
        assert contract.exchange == Exchange.NSE

    def test_contract_display_name(self, sample_option_contract):
        """Display name should be human-readable."""
        assert "NIFTY" in sample_option_contract.display_name
        assert "25000" in sample_option_contract.display_name
        assert "CE" in sample_option_contract.display_name


class TestOptionQuote:
    """Tests for timestamped option quote observations."""

    def test_quote_is_timestamped(self, sample_option_quote_ce):
        """Every quote must carry a timestamp."""
        assert sample_option_quote_ce.timestamp is not None
        assert isinstance(sample_option_quote_ce.timestamp, datetime)

    def test_quote_has_source(self, sample_option_quote_ce):
        """Every quote must identify its source."""
        assert sample_option_quote_ce.source == "test_fixture"

    def test_quote_has_data_quality(self, sample_option_quote_ce):
        """Every quote must carry data quality status."""
        assert sample_option_quote_ce.data_quality == DataQualityStatus.GOOD

    def test_negative_price_becomes_none(self):
        """Negative prices should be converted to None, not kept."""
        quote = OptionQuote(
            underlying="NIFTY",
            option_type=OptionType.CE,
            strike_price=25000.0,
            expiry_date=date(2025, 10, 2),
            last_price=-5.0,
            timestamp=datetime.now(),
            source="test",
        )
        assert quote.last_price is None  # Validator should convert to None

    def test_negative_volume_becomes_none(self):
        """Negative volume should be converted to None."""
        quote = OptionQuote(
            underlying="NIFTY",
            option_type=OptionType.CE,
            strike_price=25000.0,
            expiry_date=date(2025, 10, 2),
            volume=-100,
            timestamp=datetime.now(),
            source="test",
        )
        assert quote.volume is None

    def test_none_fields_preserved(self):
        """None fields should stay None — never filled with guesses."""
        quote = OptionQuote(
            underlying="NIFTY",
            option_type=OptionType.PE,
            strike_price=25000.0,
            expiry_date=date(2025, 10, 2),
            timestamp=datetime.now(),
            source="test",
        )
        assert quote.last_price is None
        assert quote.bid_price is None
        assert quote.ask_price is None
        assert quote.volume is None
        assert quote.open_interest is None
        assert quote.implied_volatility is None


class TestGreeksObservation:
    """Tests for the Greeks observation model (Phase 3 schema)."""

    def test_greeks_are_timestamped(self):
        """Greeks observations must be timestamped, not contract properties."""
        obs = GreeksObservation(
            underlying="NIFTY",
            option_type=OptionType.CE,
            strike_price=25000.0,
            expiry_date=date(2025, 10, 2),
            spot_price=25000.0,
            delta=0.5,
            gamma=0.001,
            timestamp=datetime.now(),
            source="test",
        )
        assert obs.timestamp is not None
        assert obs.delta == 0.5
        assert obs.pricing_model == "black_scholes"  # default


class TestImpliedVolatilityObs:
    """Tests for our own IV calculations (Phase 3 schema)."""

    def test_iv_obs_separate_from_source_iv(self):
        """Our IV calculation is separate from the data source's IV."""
        obs = ImpliedVolatilityObs(
            underlying="NIFTY",
            option_type=OptionType.CE,
            strike_price=25000.0,
            expiry_date=date(2025, 10, 2),
            spot_price=25000.0,
            iv=15.5,
            solver_method="newton_raphson",
            solver_converged=True,
            timestamp=datetime.now(),
            source="test",
        )
        assert obs.iv == 15.5
        assert obs.solver_converged is True


class TestSerialization:
    """Test JSON serialization and deserialization."""

    def test_quote_roundtrip(self, sample_option_quote_ce):
        """Serialize and deserialize should produce identical data."""
        json_str = sample_option_quote_ce.model_dump_json()
        restored = OptionQuote.model_validate_json(json_str)
        assert restored.underlying == sample_option_quote_ce.underlying
        assert restored.strike_price == sample_option_quote_ce.strike_price
        assert restored.last_price == sample_option_quote_ce.last_price

    def test_contract_roundtrip(self, sample_option_contract):
        """Contract serialization roundtrip."""
        json_str = sample_option_contract.model_dump_json()
        restored = OptionContract.model_validate_json(json_str)
        assert restored.underlying == sample_option_contract.underlying
        assert restored.lot_size == sample_option_contract.lot_size

    def test_chain_snapshot_roundtrip(self, sample_option_chain):
        """Full chain snapshot serialization."""
        json_str = sample_option_chain.model_dump_json()
        restored = OptionChainSnapshot.model_validate_json(json_str)
        assert restored.underlying == "NIFTY"
        assert len(restored.strikes) == len(sample_option_chain.strikes)
        assert restored.spot_price == sample_option_chain.spot_price
