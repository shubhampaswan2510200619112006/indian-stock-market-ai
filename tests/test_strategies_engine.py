"""
Unit tests for Strategy Construction, Decomposable Scoring, and Mandatory NO-TRADE Gating.
"""

from datetime import date, datetime, timedelta

import pytest

from src.features.market_regime import MarketRegimeResult, MarketRegimeType
from src.ingestion.schemas import DataQualityStatus, OptionChainSnapshot, OptionQuote, OptionStrikeRow, OptionType
from src.options.surface import VolatilitySurfaceResult
from src.strategies.engine import StrategyResearchEngine
from src.strategies.scoring import evaluate_and_score_strategy
from src.strategies.suitability import MarketThesis
from src.strategies.templates import StrategyBuilder


def make_test_chain(crossed: bool = False):
    exp = date.today() + timedelta(days=14)
    spot = 24000.0

    strikes_data = [
        (23800.0, 250.0, 30.0),
        (23900.0, 180.0, 50.0),
        (24000.0, 120.0, 80.0),
        (24100.0, 70.0, 130.0),
        (24200.0, 35.0, 200.0),
    ]
    rows = []

    for k, price_ce, price_pe in strikes_data:
        bid_ce, ask_ce = (price_ce - 1.0, price_ce + 1.0) if not crossed else (price_ce + 5.0, price_ce - 5.0)
        ce_q = OptionQuote(
            timestamp=datetime.now(),
            source="test",
            underlying="NIFTY",
            option_type=OptionType.CE,
            strike_price=k,
            expiry_date=exp,
            last_price=price_ce,
            bid_price=bid_ce,
            ask_price=ask_ce,
            bid_ask_spread=abs(ask_ce - bid_ce),
            implied_volatility=0.16,
        )
        pe_q = OptionQuote(
            timestamp=datetime.now(),
            source="test",
            underlying="NIFTY",
            option_type=OptionType.PE,
            strike_price=k,
            expiry_date=exp,
            last_price=price_pe,
            bid_price=price_pe - 1.0,
            ask_price=price_pe + 1.0,
            bid_ask_spread=2.0,
            implied_volatility=0.16,
        )
        rows.append(OptionStrikeRow(strike_price=k, expiry_date=exp, ce=ce_q, pe=pe_q))

    return OptionChainSnapshot(
        timestamp=datetime.now(),
        source="test",
        data_quality=DataQualityStatus.GOOD,
        underlying="NIFTY",
        expiry_date=exp,
        spot_price=spot,
        strikes=rows,
    )


def test_strategy_builder():
    chain = make_test_chain()
    builder = StrategyBuilder(chain)

    bull_call = builder.build_bull_call_spread(24000.0, 24100.0)
    assert bull_call is not None
    assert bull_call.strategy_name == "Bull Call Spread"
    assert len(bull_call.legs) == 2
    assert bull_call.legs[0].action == "BUY"
    assert bull_call.legs[1].action == "SELL"


def test_decomposable_scoring():
    chain = make_test_chain()
    builder = StrategyBuilder(chain)
    candidate = builder.build_bull_call_spread(24000.0, 24100.0)

    regime_res = MarketRegimeResult(
        symbol="NIFTY",
        timestamp=datetime.now(),
        source="test",
        data_quality=DataQualityStatus.GOOD,
        regime=MarketRegimeType.BULL,
        confidence=0.80,
    )
    surface_res = VolatilitySurfaceResult(
        timestamp=datetime.now(),
        source="test",
        underlying="NIFTY",
        spot_price=24000.0,
        expiry_date=date.today() + timedelta(days=14),
        atm_iv=0.16,
    )

    thesis = MarketThesis(
        symbol="NIFTY",
        regime=regime_res,
        surface=surface_res,
        direction_view="BULLISH",
        direction_confidence=0.80,
        volatility_view="IV_FAIR",
    )

    score = evaluate_and_score_strategy(candidate, thesis)

    assert score.overall_score > 60.0
    assert score.components.directional_alignment >= 18.0
    assert len(score.positive_evidence) > 0


def test_mandatory_no_trade_on_crossed_market():
    """
    CRITICAL MANDATORY TEST:
    If market quotes are crossed (Bid > Ask), the engine MUST trigger no_trade_decision=True!
    """
    crossed_chain = make_test_chain(crossed=True)

    regime_res = MarketRegimeResult(
        symbol="NIFTY",
        timestamp=datetime.now(),
        source="test",
        data_quality=DataQualityStatus.GOOD,
        regime=MarketRegimeType.BULL,
        confidence=0.80,
    )
    surface_res = VolatilitySurfaceResult(
        timestamp=datetime.now(),
        source="test",
        underlying="NIFTY",
        spot_price=24000.0,
        expiry_date=date.today() + timedelta(days=14),
        atm_iv=0.16,
    )
    thesis = MarketThesis(
        symbol="NIFTY",
        regime=regime_res,
        surface=surface_res,
        direction_view="BULLISH",
        direction_confidence=0.80,
        volatility_view="IV_FAIR",
    )

    engine = StrategyResearchEngine()
    result = engine.evaluate_strategies(crossed_chain, thesis)

    assert result.no_trade_decision is True
    assert "Crossed market" in "".join(result.no_trade_reasons)


def test_mandatory_no_trade_on_unavailable_data():
    """
    If option chain data is marked UNAVAILABLE, engine MUST trigger no_trade_decision=True!
    """
    empty_chain = OptionChainSnapshot(
        timestamp=datetime.now(),
        source="test",
        data_quality=DataQualityStatus.UNAVAILABLE,
        underlying="NIFTY",
        expiry_date=date.today() + timedelta(days=14),
        spot_price=24000.0,
        strikes=[],
    )
    regime_res = MarketRegimeResult(
        symbol="NIFTY",
        timestamp=datetime.now(),
        source="test",
        data_quality=DataQualityStatus.GOOD,
        regime=MarketRegimeType.UNKNOWN,
        confidence=0.0,
    )
    surface_res = VolatilitySurfaceResult(
        timestamp=datetime.now(),
        source="test",
        underlying="NIFTY",
        spot_price=24000.0,
        expiry_date=date.today() + timedelta(days=14),
    )
    thesis = MarketThesis(
        symbol="NIFTY",
        regime=regime_res,
        surface=surface_res,
        direction_view="UNCERTAIN",
        direction_confidence=0.0,
        volatility_view="IV_FAIR",
    )

    engine = StrategyResearchEngine()
    result = engine.evaluate_strategies(empty_chain, thesis)

    assert result.no_trade_decision is True
    assert len(result.no_trade_reasons) > 0
