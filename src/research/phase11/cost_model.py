"""
Phase 11 Transaction Cost and Friction Engine.

Strict separation per Methodology Corrections 1, 2, 3, 4:
1. Statutory / exchange-linked charges:
   - STT (Securities Transaction Tax): 0.1% on delivery (both buy and sell)
   - Exchange transaction charges: 0.00345%
   - SEBI turnover charges: 0.0001%
   - Stamp duty: 0.015% (on buy side only)
   - GST: 18% on (brokerage + exchange transaction fee + SEBI fee)
2. Research assumptions:
   - BROKERAGE_ASSUMPTION = 0.03% (0.0003 per leg; research assumption, not statutory)
   - SLIPPAGE_ASSUMPTION = 5.0 bps per leg (0.0005 per leg; research assumption)

Zero predetermined total drag claims:
Dynamically computes BUY_COST, SELL_COST, TOTAL_TRADE_COST, TURNOVER, TOTAL_FRICTION, NET_RETURN.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


# Research Assumptions (Not statutory facts)
BROKERAGE_ASSUMPTION: float = 0.0003       # 0.03% per leg (research assumption)
SLIPPAGE_ASSUMPTION_BPS: float = 5.0      # 5.0 bps per leg (research assumption)
SLIPPAGE_ASSUMPTION: float = 0.0005       # 0.05% per leg

# Statutory / Exchange-linked Rates (Indian Equity Delivery)
STT_DELIVERY_RATE: float = 0.001          # 0.1% on buy and sell
EXCHANGE_TURNOVER_RATE: float = 0.0000345 # 0.00345% on turnover
SEBI_TURNOVER_RATE: float = 0.000001     # 0.0001% on turnover
STAMP_DUTY_RATE: float = 0.00015          # 0.015% on buy turnover only
GST_RATE: float = 0.18                    # 18% on (brokerage + exchange + SEBI)


@dataclass
class TradeLegCost:
    side: str  # BUY or SELL
    trade_value: float
    # Statutory / Exchange charges:
    stt: float
    exchange_charges: float
    sebi_charges: float
    stamp_duty: float
    gst: float
    total_statutory_charges: float
    # Research assumptions:
    brokerage: float
    slippage: float
    total_research_assumptions: float
    # Total
    total_leg_cost: float
    total_leg_cost_bps: float


@dataclass
class RoundTripCostBreakdown:
    buy_value: float
    sell_value: float
    total_turnover: float
    buy_leg: TradeLegCost
    sell_leg: TradeLegCost
    total_statutory_cost: float
    total_brokerage: float
    total_slippage: float
    total_friction: float
    total_friction_bps: float


class IndianEquityCostModel:
    """
    Computes exact statutory charges, research assumptions, and net return deductions.
    """

    def __init__(
        self,
        brokerage_rate: float = BROKERAGE_ASSUMPTION,
        slippage_rate: float = SLIPPAGE_ASSUMPTION,
        cost_multiplier: float = 1.0,
    ):
        self.brokerage_rate = brokerage_rate * cost_multiplier
        self.slippage_rate = slippage_rate * cost_multiplier
        self.cost_multiplier = cost_multiplier

    def compute_buy_leg(self, trade_value: float) -> TradeLegCost:
        """Computes all cost items for a BUY delivery leg."""
        # Statutory & exchange fees
        stt = trade_value * STT_DELIVERY_RATE
        exchange = trade_value * EXCHANGE_TURNOVER_RATE
        sebi = trade_value * SEBI_TURNOVER_RATE
        stamp = trade_value * STAMP_DUTY_RATE

        # Research assumptions
        brokerage = trade_value * self.brokerage_rate
        slippage = trade_value * self.slippage_rate

        # GST is 18% on (brokerage + exchange + SEBI)
        gst = (brokerage + exchange + sebi) * GST_RATE

        statutory_total = stt + exchange + sebi + stamp + gst
        assumptions_total = brokerage + slippage
        total = statutory_total + assumptions_total
        bps = (total / trade_value * 10000.0) if trade_value > 0 else 0.0

        return TradeLegCost(
            side="BUY",
            trade_value=trade_value,
            stt=stt,
            exchange_charges=exchange,
            sebi_charges=sebi,
            stamp_duty=stamp,
            gst=gst,
            total_statutory_charges=statutory_total,
            brokerage=brokerage,
            slippage=slippage,
            total_research_assumptions=assumptions_total,
            total_leg_cost=total,
            total_leg_cost_bps=bps,
        )

    def compute_sell_leg(self, trade_value: float) -> TradeLegCost:
        """Computes all cost items for a SELL delivery leg."""
        # Statutory & exchange fees (Stamp duty is 0 on sell)
        stt = trade_value * STT_DELIVERY_RATE
        exchange = trade_value * EXCHANGE_TURNOVER_RATE
        sebi = trade_value * SEBI_TURNOVER_RATE
        stamp = 0.0

        # Research assumptions
        brokerage = trade_value * self.brokerage_rate
        slippage = trade_value * self.slippage_rate

        # GST on brokerage + exchange + SEBI
        gst = (brokerage + exchange + sebi) * GST_RATE

        statutory_total = stt + exchange + sebi + stamp + gst
        assumptions_total = brokerage + slippage
        total = statutory_total + assumptions_total
        bps = (total / trade_value * 10000.0) if trade_value > 0 else 0.0

        return TradeLegCost(
            side="SELL",
            trade_value=trade_value,
            stt=stt,
            exchange_charges=exchange,
            sebi_charges=sebi,
            stamp_duty=stamp,
            gst=gst,
            total_statutory_charges=statutory_total,
            brokerage=brokerage,
            slippage=slippage,
            total_research_assumptions=assumptions_total,
            total_leg_cost=total,
            total_leg_cost_bps=bps,
        )

    def compute_round_trip(self, buy_value: float, sell_value: float) -> RoundTripCostBreakdown:
        """Computes complete round-trip friction and turnover."""
        buy_leg = self.compute_buy_leg(buy_value)
        sell_leg = self.compute_sell_leg(sell_value)

        total_turnover = buy_value + sell_value
        statutory = buy_leg.total_statutory_charges + sell_leg.total_statutory_charges
        brokerage = buy_leg.brokerage + sell_leg.brokerage
        slippage = buy_leg.slippage + sell_leg.slippage
        total_friction = buy_leg.total_leg_cost + sell_leg.total_leg_cost
        avg_value = (buy_value + sell_value) / 2.0
        bps = (total_friction / avg_value * 10000.0) if avg_value > 0 else 0.0

        return RoundTripCostBreakdown(
            buy_value=buy_value,
            sell_value=sell_value,
            total_turnover=total_turnover,
            buy_leg=buy_leg,
            sell_leg=sell_leg,
            total_statutory_cost=statutory,
            total_brokerage=brokerage,
            total_slippage=slippage,
            total_friction=total_friction,
            total_friction_bps=bps,
        )

    def calculate_net_return(self, gross_return: float, turnover: float = 1.0) -> float:
        """
        Calculates net return given a gross return and turnover factor.
        turnover=1.0 represents a single full rebalance cycle (100% buy and sell).
        """
        rt = self.compute_round_trip(100.0, 100.0)
        friction_rate = (rt.total_friction / 100.0) * turnover
        return gross_return - friction_rate


if __name__ == "__main__":
    cm = IndianEquityCostModel()
    sample = cm.compute_round_trip(100000.0, 100000.0)
    print("Indian Equity Cost Model Dynamic Evaluation (1.0x baseline):")
    print(f"Buy Leg BPS: {sample.buy_leg.total_leg_cost_bps:.2f} bps")
    print(f"Sell Leg BPS: {sample.sell_leg.total_leg_cost_bps:.2f} bps")
    print(f"Total Round-Trip Friction BPS: {sample.total_friction_bps:.2f} bps")
    print(f"  - Statutory charges: {sample.total_statutory_cost:.2f} ({sample.total_statutory_cost / 100000.0 * 10000:.2f} bps)")
    print(f"  - Brokerage assumption: {sample.total_brokerage:.2f} ({sample.total_brokerage / 100000.0 * 10000:.2f} bps)")
    print(f"  - Slippage assumption: {sample.total_slippage:.2f} ({sample.total_slippage / 100000.0 * 10000:.2f} bps)")
