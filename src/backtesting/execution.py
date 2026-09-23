"""
Realistic Order Execution Engine & Indian Options Transaction Fee Calculator.

EXECUTION MODEL:
- BUY: Ask + Slippage
- SELL: Bid - Slippage
- Multi-leg execution tracked per leg.
"""

from __future__ import annotations

import math
from typing import Tuple
from src.ingestion.schemas import OptionQuote, OptionType
from src.backtesting.models import ExecutionCostModel, LiquidityMode


def calculate_execution_price(
    quote: OptionQuote,
    action: str,  # BUY or SELL
    cost_model: ExecutionCostModel,
) -> float:
    """
    Computes realistic execution price for a leg given market quote and action.
    """
    bid = quote.bid_price if quote.bid_price is not None else quote.last_price
    ask = quote.ask_price if quote.ask_price is not None else quote.last_price
    ltp = quote.last_price

    # Fallback when bid/ask is invalid
    if bid is None or ask is None or bid <= 0 or ask <= 0:
        bid = ltp * 0.99
        ask = ltp * 1.01

    if action.upper() == "BUY":
        base_price = ask
        # Slippage added to ask
        exec_price = base_price * (1.0 + cost_model.slippage_pct)
    else:  # SELL
        base_price = bid
        # Slippage subtracted from bid
        exec_price = base_price * (1.0 - cost_model.slippage_pct)

    return max(0.05, round(exec_price, 2))


def calculate_nse_option_transaction_costs(
    premium: float,
    quantity: int,
    lots: int,
    action: str,  # BUY or SELL
    cost_model: ExecutionCostModel,
) -> float:
    """
    Calculates exact NSE options transaction costs (Brokerage, STT, Exchange fee, GST, SEBI charges).
    
    Taxes breakdown:
    - Brokerage: INR 20 per lot (or configured amount)
    - STT: 0.0625% on sell side premium
    - Exchange Turnover Charge: 0.053% on premium
    - GST: 18% on (Brokerage + Exchange Fee)
    - SEBI Turnover Fee: 0.0001% on premium
    """
    turnover = max(0.0, premium * quantity)
    
    # 1. Brokerage
    brokerage = cost_model.brokerage_per_lot * lots
    
    # 2. STT (Securities Transaction Tax) — charged ONLY on sell side premium for options in India
    stt = (turnover * cost_model.stt_rate_pct) if action.upper() == "SELL" else 0.0
    
    # 3. Exchange transaction fee
    exchange_fee = turnover * cost_model.exchange_fee_pct
    
    # 4. GST (18% on Brokerage + Exchange Fee)
    gst = (brokerage + exchange_fee) * cost_model.gst_rate_pct
    
    # 5. SEBI turnover charge
    sebi_fee = turnover * cost_model.sebi_fee_pct

    # 6. Stamp duty — charged on BUY side only (0.003% of premium, Phase 17 fix)
    stamp_duty = (turnover * cost_model.stamp_duty_rate_pct) if action.upper() == "BUY" else 0.0
    
    total_cost = brokerage + stt + exchange_fee + gst + sebi_fee + stamp_duty
    return round(total_cost, 2)


def evaluate_liquidity_filter(
    quote: OptionQuote,
    mode: LiquidityMode,
) -> Tuple[bool, str]:
    """
    Evaluates whether an option quote satisfies liquidity requirements for execution.
    """
    if quote.volume is None or quote.open_interest is None:
        return False, "Missing volume or open interest"

    bid = quote.bid_price or quote.last_price
    ask = quote.ask_price or quote.last_price

    if bid is None or ask is None or bid <= 0 or ask <= 0:
        return False, "Invalid bid/ask prices"

    if bid > ask:
        return False, "Crossed market (Bid > Ask)"

    mid = (bid + ask) / 2.0
    spread_pct = (ask - bid) / max(0.01, mid)

    if mode == LiquidityMode.STRICT:
        if quote.open_interest < 1000:
            return False, f"OI {quote.open_interest} below strict limit (1000)"
        if quote.volume < 100:
            return False, f"Volume {quote.volume} below strict limit (100)"
        if spread_pct > 0.05:  # 5% max spread
            return False, f"Spread {spread_pct:.1%} exceeds strict limit (5%)"

    elif mode == LiquidityMode.NORMAL:
        if quote.open_interest < 200:
            return False, f"OI {quote.open_interest} below normal limit (200)"
        if quote.volume < 20:
            return False, f"Volume {quote.volume} below normal limit (20)"
        if spread_pct > 0.12:  # 12% max spread
            return False, f"Spread {spread_pct:.1%} exceeds normal limit (12%)"

    elif mode == LiquidityMode.RELAXED:
        if quote.open_interest < 50:
            return False, f"OI {quote.open_interest} below relaxed limit (50)"
        if spread_pct > 0.25:  # 25% max spread
            return False, f"Spread {spread_pct:.1%} exceeds relaxed limit (25%)"

    return True, "Liquidity filter passed"
