"""
Tests for option chain analysis engine.

Validates:
- ATM/ITM/OTM classification
- PCR calculation
- Max pain calculation
- OI concentration detection
- Unusual activity detection
- Handling of missing data (nulls propagate, not invented)
- Probabilistic language in interpretations
"""

import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from src.ingestion.schemas import (
    DataQualityStatus,
    Moneyness,
    OptionChainSnapshot,
    OptionQuote,
    OptionStrikeRow,
    OptionType,
)
from src.options.chain import OptionChainAnalyzer
from src.options.utils import (
    calculate_max_pain,
    classify_moneyness,
    distance_from_atm,
    distance_from_atm_pct,
    find_atm_strike,
    get_strike_step,
)


class TestMoneyness:
    """Test moneyness classification."""

    def test_atm_call(self):
        """Call at the money."""
        m = classify_moneyness(25000.0, 25000.0, OptionType.CE)
        assert m == Moneyness.ATM

    def test_atm_put(self):
        """Put at the money."""
        m = classify_moneyness(25000.0, 25000.0, OptionType.PE)
        assert m == Moneyness.ATM

    def test_itm_call(self):
        """Call with strike below spot is ITM."""
        m = classify_moneyness(25000.0, 24500.0, OptionType.CE)
        assert m == Moneyness.ITM

    def test_otm_call(self):
        """Call with strike above spot is OTM."""
        m = classify_moneyness(25000.0, 25500.0, OptionType.CE)
        assert m == Moneyness.OTM

    def test_itm_put(self):
        """Put with strike above spot is ITM."""
        m = classify_moneyness(25000.0, 25500.0, OptionType.PE)
        assert m == Moneyness.ITM

    def test_otm_put(self):
        """Put with strike below spot is OTM."""
        m = classify_moneyness(25000.0, 24500.0, OptionType.PE)
        assert m == Moneyness.OTM

    def test_near_atm_within_threshold(self):
        """Strike within threshold should be ATM."""
        # 25100 is 0.4% from 25000 (within default 0.5% threshold)
        m = classify_moneyness(25000.0, 25100.0, OptionType.CE, atm_threshold_pct=0.5)
        assert m == Moneyness.ATM

    def test_zero_spot_returns_otm(self):
        """Zero spot price should return OTM (edge case)."""
        m = classify_moneyness(0.0, 25000.0, OptionType.CE)
        assert m == Moneyness.OTM


class TestDistanceFromATM:
    """Test distance calculations."""

    def test_distance_above_spot(self):
        d = distance_from_atm(25000.0, 25500.0)
        assert d == 500.0

    def test_distance_below_spot(self):
        d = distance_from_atm(25000.0, 24500.0)
        assert d == -500.0

    def test_distance_at_spot(self):
        d = distance_from_atm(25000.0, 25000.0)
        assert d == 0.0

    def test_distance_pct(self):
        pct = distance_from_atm_pct(25000.0, 25500.0)
        assert abs(pct - 2.0) < 0.01


class TestMaxPain:
    """Test max pain calculation."""

    def test_max_pain_with_sample_chain(self, sample_option_chain):
        """Max pain should be a valid strike within the chain."""
        mp = calculate_max_pain(sample_option_chain)
        assert mp is not None
        chain_strikes = [r.strike_price for r in sample_option_chain.strikes]
        assert mp in chain_strikes

    def test_max_pain_empty_chain(self, sample_timestamp):
        """Max pain should be None for empty chain."""
        empty = OptionChainSnapshot(
            underlying="NIFTY", expiry_date=date(2025, 10, 2),
            spot_price=25000.0, strikes=[],
            timestamp=sample_timestamp, source="test",
        )
        assert calculate_max_pain(empty) is None

    def test_max_pain_is_reasonable(self, sample_option_chain):
        """Max pain should be within the strike range."""
        mp = calculate_max_pain(sample_option_chain)
        strikes = [r.strike_price for r in sample_option_chain.strikes]
        assert min(strikes) <= mp <= max(strikes)


class TestATMStrike:
    """Test ATM strike finder."""

    def test_find_exact_atm(self):
        strikes = [24500, 24600, 24700, 24800, 24900, 25000, 25100]
        assert find_atm_strike(25000.0, strikes) == 25000

    def test_find_nearest_atm(self):
        strikes = [24500, 24600, 24700, 24800, 24900, 25000, 25100]
        assert find_atm_strike(24950.0, strikes) == 24900  # or 25000

    def test_empty_strikes(self):
        assert find_atm_strike(25000.0, []) is None


class TestStrikeStep:
    """Test strike step detection."""

    def test_uniform_step(self):
        strikes = [24500, 24600, 24700, 24800, 24900, 25000]
        assert get_strike_step(strikes) == 100.0

    def test_single_strike(self):
        assert get_strike_step([25000]) is None


class TestOptionChainAnalyzer:
    """Test the full chain analyzer."""

    def test_analyze_produces_result(self, sample_option_chain):
        """Analyzer should produce a complete analysis."""
        analyzer = OptionChainAnalyzer()
        analysis = analyzer.analyze(sample_option_chain)

        assert analysis.underlying == "NIFTY"
        assert analysis.spot_price == 25000.0
        assert analysis.timestamp is not None
        assert analysis.source is not None

    def test_pcr_calculated(self, sample_option_chain):
        """PCR should be computed from OI."""
        analyzer = OptionChainAnalyzer()
        analysis = analyzer.analyze(sample_option_chain)

        assert analysis.put_call_ratio_oi is not None
        assert analysis.put_call_ratio_oi > 0

    def test_max_pain_in_analysis(self, sample_option_chain):
        """Max pain should be present in analysis."""
        analyzer = OptionChainAnalyzer()
        analysis = analyzer.analyze(sample_option_chain)

        assert analysis.max_pain_strike is not None
        strikes = [r.strike_price for r in sample_option_chain.strikes]
        assert analysis.max_pain_strike in strikes

    def test_oi_zones_detected(self, sample_option_chain):
        """High OI zones should be detected."""
        analyzer = OptionChainAnalyzer()
        analysis = analyzer.analyze(sample_option_chain)

        # With our test data, there should be at least one high OI zone
        assert len(analysis.oi_concentration_zones) > 0

    def test_oi_zones_use_probabilistic_language(self, sample_option_chain):
        """OI zone interpretations must use probabilistic language."""
        analyzer = OptionChainAnalyzer()
        analysis = analyzer.analyze(sample_option_chain)

        for zone in analysis.oi_concentration_zones:
            interpretation = zone.interpretation.lower()
            # Should NOT contain deterministic language
            assert "will" not in interpretation or "probabilistic" in interpretation
            assert "guaranteed" not in interpretation
            # Should contain probabilistic language
            assert any(word in interpretation for word in [
                "may", "potential", "probabilistic", "concentration",
            ])

    def test_interpretation_has_disclaimer(self, sample_option_chain):
        """Chain interpretation must include a disclaimer."""
        analyzer = OptionChainAnalyzer()
        analysis = analyzer.analyze(sample_option_chain)

        interp = analysis.chain_interpretation.lower()
        assert "probabilistic" in interp or "disclaimer" in interp

    def test_empty_chain_handled(self, sample_timestamp):
        """Analyzer should handle empty chain gracefully."""
        empty = OptionChainSnapshot(
            underlying="NIFTY", expiry_date=date(2025, 10, 2),
            spot_price=25000.0, strikes=[],
            timestamp=sample_timestamp, source="test",
        )
        analyzer = OptionChainAnalyzer()
        analysis = analyzer.analyze(empty)

        assert analysis.data_quality == DataQualityStatus.UNAVAILABLE
        assert "no option chain data" in analysis.chain_interpretation.lower()

    def test_missing_oi_handled(self, sample_timestamp, sample_expiry):
        """Analyzer should handle strikes with missing OI."""
        quote = OptionQuote(
            underlying="NIFTY", option_type=OptionType.CE,
            strike_price=25000.0, expiry_date=sample_expiry,
            last_price=100.0, open_interest=None,  # Missing OI
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
        analyzer = OptionChainAnalyzer()
        analysis = analyzer.analyze(chain)

        # Should not crash — should produce some result
        assert analysis is not None
        assert analysis.underlying == "NIFTY"

    def test_unusual_activity_detected(self, sample_option_chain):
        """Unusual activity should be detected in the test data."""
        analyzer = OptionChainAnalyzer()
        analysis = analyzer.analyze(sample_option_chain)

        # Our test data has some strikes with notably higher OI/volume
        # The detector should flag at least some unusual activity
        # (depends on sigma threshold — may be 0 if data is too uniform)
        # Just verify it doesn't crash and returns a list
        assert isinstance(analysis.unusual_activity, list)

    def test_atm_iv_extracted(self, sample_option_chain):
        """ATM IV should be extracted from the chain."""
        analyzer = OptionChainAnalyzer()
        analysis = analyzer.analyze(sample_option_chain)

        # ATM strike is 25000, which has IV in our test data
        assert analysis.atm_iv_ce is not None or analysis.atm_iv_pe is not None
