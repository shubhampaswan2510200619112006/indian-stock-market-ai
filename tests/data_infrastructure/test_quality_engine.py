"""
Tests for Phase 9 Data Quality & Quarantine Engine.
"""

from datetime import date, datetime, timedelta, timezone
import pytest

from src.data_infrastructure.models import (
    DataStatus,
    MarketObservation,
    ObservationTimestamps,
    OptionObservation,
)
from src.data_infrastructure.quality_engine import DataQualityEngine


def test_quarantine_negative_market_price():
    now = datetime.now(timezone.utc)
    obs = MarketObservation(
        observation_id="TEST-OBS-1",
        provider="TEST",
        provider_symbol="TEST",
        symbol="NIFTY",
        timestamps=ObservationTimestamps(provider_timestamp=now, received_timestamp=now),
        last_price=-10.0,  # Negative price!
        data_status=DataStatus.HISTORICAL,
    )
    res = DataQualityEngine.validate_and_quarantine_market_obs(obs)
    assert res.is_valid is False
    assert res.rule_violated == "NON_POSITIVE_PRICE"
    assert res.severity == "QUARANTINE"


def test_quarantine_crossed_market_observation():
    now = datetime.now(timezone.utc)
    obs = MarketObservation(
        observation_id="TEST-OBS-2",
        provider="TEST",
        provider_symbol="TEST",
        symbol="NIFTY",
        timestamps=ObservationTimestamps(provider_timestamp=now, received_timestamp=now),
        last_price=22000.0,
        bid_price=22100.0,  # Bid > Ask
        ask_price=22000.0,
        data_status=DataStatus.VERIFIED_DELAYED,
    )
    res = DataQualityEngine.validate_and_quarantine_market_obs(obs)
    assert res.is_valid is False
    assert res.rule_violated == "CROSSED_MARKET"


def test_quarantine_impossible_option_strike():
    now = datetime.now(timezone.utc)
    obs = OptionObservation(
        observation_id="OPT-OBS-1",
        contract_id="C1",
        contract_symbol="NIFTY_CE_0",
        underlying="NIFTY",
        expiry_date=date(2025, 12, 31),
        strike_price=-500.0,  # Impossible strike!
        option_type="CE",
        timestamps=ObservationTimestamps(provider_timestamp=now, received_timestamp=now),
    )
    res = DataQualityEngine.validate_and_quarantine_option_obs(obs)
    assert res.is_valid is False
    assert res.rule_violated == "IMPOSSIBLE_STRIKE"


def test_quarantine_observation_post_expiry():
    obs_time = datetime(2025, 2, 1, 10, 0, tzinfo=timezone.utc)
    obs = OptionObservation(
        observation_id="OPT-OBS-2",
        contract_id="C2",
        contract_symbol="NIFTY_CE_22000",
        underlying="NIFTY",
        expiry_date=date(2025, 1, 30),  # Expired before observation!
        strike_price=22000.0,
        option_type="CE",
        timestamps=ObservationTimestamps(provider_timestamp=obs_time, received_timestamp=obs_time),
    )
    res = DataQualityEngine.validate_and_quarantine_option_obs(obs)
    assert res.is_valid is False
    assert res.rule_violated == "OBSERVATION_POST_EXPIRY"


def test_component_quality_scores_calculation():
    scores = DataQualityEngine.calculate_dataset_quality_scores(
        observations_count=1000,
        quarantined_count=5,
        bid_ask_coverage_pct=0.0,
        timestamp_valid_pct=99.5,
        provider_verified=True,
    )
    d = scores.to_dict()
    assert d["completeness"] == "99.5%"
    assert d["timestamp_integrity"] == "99.5%"
    assert d["overall_status"] == "PARTIALLY_VALIDATED"
    assert any("Bid/Ask coverage is 0%" in w for w in d["warnings"])
