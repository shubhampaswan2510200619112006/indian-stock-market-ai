"""
Unit tests for Price Action pattern engine.
"""

from datetime import datetime, timedelta

import pandas as pd
import pytest

from src.features.price_action import PriceActionEngine
from src.ingestion.schemas import TimeFrame


def make_df(rows):
    """Helper to create OHLCV DataFrame from list of tuples (open, high, low, close, volume)."""
    dates = [datetime(2026, 1, 1) + timedelta(days=i) for i in range(len(rows))]
    data = []
    for d, (o, h, l, c, v) in zip(dates, rows):
        data.append({"timestamp": d, "open": o, "high": h, "low": l, "close": c, "volume": v})
    return pd.DataFrame(data)


def test_doji_detection():
    # 5 neutral bars, last bar is Doji (O=100, H=110, L=90, C=100.1)
    rows = [(100, 105, 95, 101, 1000)] * 5
    rows.append((100.0, 110.0, 90.0, 100.1, 1000))
    df = make_df(rows)

    engine = PriceActionEngine(timeframe=TimeFrame.DAILY)
    patterns = engine.detect_patterns(df)

    p_names = [p.pattern for p in patterns]
    assert "Doji" in p_names

    doji_pat = next(p for p in patterns if p.pattern == "Doji")
    assert doji_pat.confidence == 0.60
    assert "invalidation_conditions" in doji_pat.model_dump()
    assert doji_pat.invalidation_conditions != ""


def test_hammer_detection():
    # Downtrend bar, then Hammer: O=100, H=101, L=80, C=99
    rows = [(105, 106, 98, 100, 1000)] * 5
    rows.append((100.0, 101.0, 80.0, 99.0, 1000))
    df = make_df(rows)

    engine = PriceActionEngine(timeframe=TimeFrame.DAILY)
    patterns = engine.detect_patterns(df)

    p_names = [p.pattern for p in patterns]
    assert "Hammer" in p_names

    hammer_pat = next(p for p in patterns if p.pattern == "Hammer")
    assert hammer_pat.confidence >= 0.70
    assert "80.00" in hammer_pat.invalidation_conditions


def test_shooting_star_detection():
    # Uptrend bar, then Shooting Star: O=100, H=120, L=99, C=101
    rows = [(90, 95, 89, 94, 1000)] * 5
    rows.append((100.0, 120.0, 99.0, 101.0, 1000))
    df = make_df(rows)

    engine = PriceActionEngine(timeframe=TimeFrame.DAILY)
    patterns = engine.detect_patterns(df)

    p_names = [p.pattern for p in patterns]
    assert "Shooting Star" in p_names


def test_bullish_engulfing_detection():
    rows = [(100, 105, 95, 100, 1000)] * 4
    # Bearish bar: O=100, C=90
    rows.append((100.0, 102.0, 89.0, 90.0, 1000))
    # Bullish engulfing bar: O=89, C=102
    rows.append((89.0, 105.0, 88.0, 102.0, 2000))
    df = make_df(rows)

    engine = PriceActionEngine(timeframe=TimeFrame.DAILY)
    patterns = engine.detect_patterns(df)

    p_names = [p.pattern for p in patterns]
    assert "Bullish Engulfing" in p_names


def test_inside_bar_detection():
    rows = [(100, 105, 95, 100, 1000)] * 4
    # Mother bar: H=120, L=80
    rows.append((100.0, 120.0, 80.0, 110.0, 1000))
    # Inside bar: H=110, L=90 (fits strictly inside 120 / 80)
    rows.append((95.0, 110.0, 90.0, 105.0, 1000))
    df = make_df(rows)

    engine = PriceActionEngine(timeframe=TimeFrame.DAILY)
    patterns = engine.detect_patterns(df)

    p_names = [p.pattern for p in patterns]
    assert "Inside Bar" in p_names


def test_gap_up_detection():
    rows = [(100, 105, 95, 100, 1000)] * 5
    # Previous high = 105
    # Current low = 110 (Gap Up!)
    rows.append((112.0, 120.0, 110.0, 118.0, 3000))
    df = make_df(rows)

    engine = PriceActionEngine(timeframe=TimeFrame.DAILY)
    patterns = engine.detect_patterns(df)

    p_names = [p.pattern for p in patterns]
    assert "Gap Up" in p_names


def test_scan_all_patterns():
    rows = [(100, 105, 95, 101, 1000)] * 5
    # Add a Hammer
    rows.append((100.0, 101.0, 80.0, 99.0, 1000))
    # Add an Engulfing
    rows.append((98.0, 105.0, 97.0, 104.0, 1500))
    df = make_df(rows)

    engine = PriceActionEngine(timeframe=TimeFrame.DAILY)
    scanned = engine.scan_all_patterns(df, max_bars=10)

    assert len(scanned) >= 1
    patterns_found = [s["pattern"] for s in scanned]
    assert "Hammer" in patterns_found or "Bullish Engulfing" in patterns_found
    for s in scanned:
        assert "marker" in s
        assert "color" in s
        assert "type" in s


def test_get_key_levels():
    rows = [
        (100, 110, 90, 105, 1000),
        (105, 115, 100, 112, 1200),
        (112, 120, 108, 118, 1500),
        (118, 122, 115, 121, 1100),
    ] * 5
    df = make_df(rows)

    engine = PriceActionEngine(timeframe=TimeFrame.DAILY)
    levels = engine.get_key_levels(df)

    assert levels["resistance_20"] >= 120.0
    assert levels["support_20"] <= 95.0
    assert "market_structure" in levels
    assert levels["distance_to_resistance_pts"] >= 0.0

