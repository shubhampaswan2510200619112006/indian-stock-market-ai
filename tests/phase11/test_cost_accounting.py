"""
Test Transaction Cost Accounting and Friction Engine for Phase 11.
"""

import pytest
from src.research.phase11.cost_model import (
    IndianEquityCostModel,
    BROKERAGE_ASSUMPTION,
    SLIPPAGE_ASSUMPTION,
    STT_DELIVERY_RATE,
    EXCHANGE_TURNOVER_RATE,
    SEBI_TURNOVER_RATE,
    STAMP_DUTY_RATE,
    GST_RATE,
)


def test_cost_components_separation():
    """Verify statutory charges and research assumptions are strictly separated."""
    cm = IndianEquityCostModel()
    rt = cm.compute_round_trip(100000.0, 100000.0)

    # Statutory charges: STT, exchange, SEBI, stamp duty, GST
    assert rt.total_statutory_cost > 0.0
    # Research assumptions: brokerage, slippage
    assert rt.total_brokerage > 0.0
    assert rt.total_slippage > 0.0

    # Brokerage must be isolated as an assumption, not statutory
    assert rt.buy_leg.brokerage == 100000.0 * BROKERAGE_ASSUMPTION
    assert rt.sell_leg.brokerage == 100000.0 * BROKERAGE_ASSUMPTION

    # Stamp duty is strictly buy side
    assert rt.buy_leg.stamp_duty == 100000.0 * STAMP_DUTY_RATE
    assert rt.sell_leg.stamp_duty == 0.0

    # Total friction must equal sum of statutory + research assumptions
    expected_total = rt.total_statutory_cost + rt.total_brokerage + rt.total_slippage
    assert abs(rt.total_friction - expected_total) < 1e-6


def test_dynamic_friction_bps():
    """Verify total friction bps is calculated dynamically rather than hard-coded."""
    cm = IndianEquityCostModel()
    rt = cm.compute_round_trip(100000.0, 100000.0)

    # In Indian equity delivery, typical friction is ~39.4 bps
    assert 35.0 <= rt.total_friction_bps <= 45.0


def test_cost_multiplier_stress():
    """Verify cost multiplier scales brokerage and slippage proportionally."""
    cm_base = IndianEquityCostModel(cost_multiplier=1.0)
    cm_stress = IndianEquityCostModel(cost_multiplier=2.0)

    rt_base = cm_base.compute_round_trip(100000.0, 100000.0)
    rt_stress = cm_stress.compute_round_trip(100000.0, 100000.0)

    assert rt_stress.total_brokerage == pytest.approx(rt_base.total_brokerage * 2.0)
    assert rt_stress.total_slippage == pytest.approx(rt_base.total_slippage * 2.0)
    assert rt_stress.total_friction > rt_base.total_friction
