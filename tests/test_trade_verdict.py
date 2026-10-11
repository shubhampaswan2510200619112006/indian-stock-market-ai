"""
Unit tests for TradeVerdictEngine and deterministic rule-based gating.
"""

from datetime import datetime, time
import pytest

from src.features.trade_verdict import MarketSnapshot, TradeVerdictEngine


@pytest.fixture
def verdict_engine():
    return TradeVerdictEngine()


def test_market_closed_triggers_caution(verdict_engine):
    """Verify that when exchange is closed, verdict defaults to caution with appropriate reason."""
    snapshot = MarketSnapshot(
        nifty_price=24200.0,
        vix_value=13.5,
        is_market_open=False,
        session_state="MARKET_CLOSED",
        regime_tag="Trending Up",
    )
    result = verdict_engine.evaluate_verdict(snapshot)
    assert result.verdict == "CAUTION"
    assert len(result.top_reasons) == 3
    assert any("CLOSED" in r for r in result.top_reasons)


def test_first_15_minutes_triggers_no_trade(verdict_engine):
    """Verify that the first 15 minutes of market open (09:15-09:30) forces NO TRADE."""
    snapshot = MarketSnapshot(
        is_market_open=True,
        session_state="FIRST_15_MINUTES",
        vix_value=14.0,
    )
    result = verdict_engine.evaluate_verdict(snapshot)
    assert result.verdict == "NO TRADE"
    assert result.is_trade_allowed is False
    assert any("First 15 minutes" in r for r in result.top_reasons)


def test_expiry_last_hour_triggers_no_trade(verdict_engine):
    """Verify that expiry day final hour forces NO TRADE due to severe gamma risk."""
    snapshot = MarketSnapshot(
        is_market_open=True,
        session_state="EXPIRY_LAST_HOUR",
        vix_value=14.0,
    )
    result = verdict_engine.evaluate_verdict(snapshot)
    assert result.verdict == "NO TRADE"
    assert result.is_trade_allowed is False
    assert any("Expiry day final hour" in r for r in result.top_reasons)


def test_high_vix_triggers_no_trade(verdict_engine):
    """Verify that India VIX >= 22.0 triggers NO TRADE."""
    snapshot = MarketSnapshot(
        is_market_open=True,
        session_state="NORMAL_HOURS",
        vix_value=24.5,
        vix_change_pct=10.0,
    )
    result = verdict_engine.evaluate_verdict(snapshot)
    assert result.verdict == "NO TRADE"
    assert any("Extreme Volatility Risk" in r for r in result.top_reasons)


def test_circuit_breaker_forces_no_trade(verdict_engine):
    """Verify that active account circuit breaker immediately halts trading."""
    snapshot = MarketSnapshot(
        is_market_open=True,
        session_state="NORMAL_HOURS",
        vix_value=13.0,
    )
    result = verdict_engine.evaluate_verdict(snapshot, breaker_active=True)
    assert result.verdict == "NO TRADE"
    assert any("circuit breaker is ACTIVE" in r for r in result.top_reasons)


def test_good_to_trade_optimal_conditions(verdict_engine):
    """Verify that normal session, sweet-spot VIX, and clear regime produces GOOD TO TRADE."""
    snapshot = MarketSnapshot(
        is_market_open=True,
        session_state="NORMAL_HOURS",
        vix_value=13.2,
        vix_change_pct=-1.5,
        regime_tag="Trending Up",
        regime_confidence=0.85,
        fii_net_cr=500.0,
        dii_net_cr=350.0,
    )
    result = verdict_engine.evaluate_verdict(snapshot, breaker_active=False, daily_loss_pct=0.0)
    assert result.verdict == "GOOD TO TRADE"
    assert result.badge_color == "#10b981"
    assert result.is_trade_allowed is True
    assert len(result.top_reasons) == 3
    assert any("Favorable Trend" in r for r in result.top_reasons)
