"""
Unit Tests for Trade Card, Liquidity Gating, Position Sizing, and NSE Transaction Costs.
"""

import pytest
from datetime import date, timedelta
from src.ingestion.schemas import OptionType
from src.features.trade_card import (
    evaluate_liquidity,
    calculate_nse_charges,
    compute_position_sizing,
    build_trade_idea,
    generate_curated_trade_ideas,
    get_nse_lot_size,
)


def test_lot_size_lookup():
    assert get_nse_lot_size("NIFTY") == 25
    assert get_nse_lot_size("BANKNIFTY") == 15
    assert get_nse_lot_size("RELIANCE") == 250
    assert get_nse_lot_size("HDFCBANK") == 550
    # Unknown fallback
    assert get_nse_lot_size("UNKNOWN_SYM") == 250


def test_liquidity_evaluation_valid_quote():
    liq = evaluate_liquidity(
        symbol="NIFTY",
        bid=100.0,
        ask=101.0,
        volume=50000,
        open_interest=250000,
    )
    assert liq.is_liquid is True
    assert len(liq.rejection_reasons) == 0
    assert liq.spread_pct < 0.02


def test_liquidity_rejection_wide_spread():
    # Index max spread is 3.5%. Here spread is ~10% (100 vs 110)
    liq = evaluate_liquidity(
        symbol="NIFTY",
        bid=100.0,
        ask=110.0,
        volume=50000,
        open_interest=250000,
    )
    assert liq.is_liquid is False
    assert any("spread" in r.lower() for r in liq.rejection_reasons)


def test_liquidity_rejection_low_volume_and_oi():
    liq = evaluate_liquidity(
        symbol="NIFTY",
        bid=50.0,
        ask=51.0,
        volume=10,  # Below 100 limit
        open_interest=200,  # Below 1000 limit
    )
    assert liq.is_liquid is False
    assert any("volume" in r.lower() for r in liq.rejection_reasons)
    assert any("open interest" in r.lower() for r in liq.rejection_reasons)


def test_liquidity_rejection_crossed_market():
    liq = evaluate_liquidity(
        symbol="NIFTY",
        bid=105.0,
        ask=100.0,
        volume=10000,
        open_interest=50000,
    )
    assert liq.is_liquid is False
    assert any("crossed" in r.lower() for r in liq.rejection_reasons)


def test_nse_transaction_costs_exact_breakdown():
    # Test 1 lot of Nifty (25 qty), Entry = ₹100, Target 1 = ₹150, Target 2 = ₹200
    qty = 25
    lots = 1
    entry = 100.0
    t1 = 150.0
    t2 = 200.0

    costs = calculate_nse_charges(
        entry_price=entry,
        target_1=t1,
        target_2=t2,
        quantity=qty,
        lots=lots,
        is_buy_first=True,
    )

    # Brokerage = 2 orders * ₹20 = ₹40.0
    assert costs.brokerage == 40.0

    # Buy turnover = 100 * 25 = 2,500
    # Sell turnover at T1 = 150 * 25 = 3,750
    # Total turnover = 6,250
    # STT = 0.0625% on sell turnover = 3750 * 0.000625 = ₹2.34375 -> ~2.34
    assert pytest.approx(costs.stt, 0.05) == 2.34

    # Exchange fee = 6250 * 0.00053 = ₹3.3125
    assert pytest.approx(costs.exchange_fee, 0.05) == 3.31

    # GST = 18% on (40.0 + 3.3125) = 0.18 * 43.3125 = ₹7.80
    assert pytest.approx(costs.gst, 0.05) == 7.80

    # Stamp duty = 0.003% on buy turnover = 2500 * 0.00003 = ₹0.075 -> ~0.08
    assert pytest.approx(costs.stamp_duty, abs=0.02) == 0.08

    # SEBI charges = 6250 * 0.000001 = ₹0.006 -> ~0.01
    assert pytest.approx(costs.sebi_charges, abs=0.02) == 0.01

    # Total charges should be sum of parts
    expected_total = (
        costs.brokerage
        + costs.stt
        + costs.exchange_fee
        + costs.gst
        + costs.stamp_duty
        + costs.sebi_charges
    )
    assert pytest.approx(costs.total_charges, 0.1) == expected_total

    # Gross P&L at T1 = (150 - 100) * 25 = ₹1,250.0
    assert costs.gross_t1_pnl == 1250.0
    # Net P&L at T1 = Gross - Total Charges
    assert pytest.approx(costs.net_t1_pnl, 0.05) == (1250.0 - costs.total_charges)


def test_position_sizing_calculation():
    # Capital ₹5,00,000, 1% risk = ₹5,000 max risk
    # Option entry = ₹100, Stop Loss = ₹70 (risk = ₹30/share)
    # Lot size = 25 -> risk per lot = 30 * 25 + ~40 charges = ~790
    # Suggested lots = floor(5000 / 790) = 6 lots
    sizing = compute_position_sizing(
        capital=500000.0,
        risk_pct=1.0,
        entry_price=100.0,
        stop_loss=70.0,
        lot_size=25,
    )

    assert sizing.max_risk_amount == 5000.0
    assert sizing.suggested_lots >= 1
    assert sizing.suggested_quantity == sizing.suggested_lots * 25
    assert sizing.max_loss_rupees <= 5100.0  # Within tolerance
    assert sizing.breakeven_price > 100.0  # Incorporates transaction fees


def test_build_trade_idea_and_why_not_warnings():
    exp = date.today() + timedelta(days=4)
    idea = build_trade_idea(
        symbol="NIFTY",
        strategy_name="NIFTY Momentum Call",
        direction_tag="CALL (BULLISH)",
        option_type=OptionType.CE,
        strike=25000.0,
        expiry_date=exp,
        spot_price=24950.0,
        premium=120.0,
        bid=119.5,
        ask=120.5,
        volume=50000,
        open_interest=2000000,
        iv=0.15,
        iv_percentile=40.0,
        confidence_score=75.0,
        reasons_fired=["Trendline breakout", "RSI above 60"],
        why_not_to_take=["Theta decay accelerates past Tuesday", "Overnight event risk"],
    )

    assert idea.is_executable is True
    assert idea.contract.lot_size == 25
    assert len(idea.why_not_to_take) >= 2
    assert idea.costs.total_charges > 0
    assert idea.plan.target_1 > idea.plan.entry_price


def test_curated_ideas_demonstrates_illiquid_rejection():
    ideas = generate_curated_trade_ideas("NIFTY")
    assert len(ideas) >= 3

    # First idea (Liquid ATM Call) should be executable
    assert ideas[0].is_executable is True

    # Far OTM lottery call should be strictly rejected due to wide spread and low volume
    illiquid_idea = ideas[2]
    assert illiquid_idea.is_executable is False
    assert illiquid_idea.liquidity.is_liquid is False
    assert len(illiquid_idea.liquidity.rejection_reasons) > 0
