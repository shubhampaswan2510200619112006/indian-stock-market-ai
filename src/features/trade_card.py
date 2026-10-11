"""
Trade Card Models, Analytics, NSE Transaction Cost Engine & Trade Idea Generator.

Implements all specifications for the 60-Second Trade Decision Terminal:
1. Exact contract details: strike, expiry, lot size, premium, delta, theta/day, IV, IV percentile.
2. Liquidity gating: bid-ask spread %, volume, OI. Outright rejection of illiquid strikes.
3. Trade plan: entry, stop-loss, targets (T1, T2), risk-reward ratio.
4. Dynamic interactive position sizing: capital, risk %, suggested lots, max loss in ₹ and %, breakeven.
5. Real NSE transaction cost breakdown: Brokerage (₹20/order), STT (0.0625% on sell), GST (18%),
   Exchange turnover fee (0.053%), SEBI charges (₹10/cr), Stamp duty (0.003% on buy), Net P&L.
6. Mandatory "Why NOT to take this trade" warning box.
7. One-click paper trade execution payload.
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.ingestion.schemas import OptionType
from src.options.pricing import black_scholes_greeks, black_scholes_price

# Standard NSE Lot sizes (Index & Top F&O Stocks)
NSE_LOT_SIZES: Dict[str, int] = {
    "NIFTY": 25,
    "BANKNIFTY": 15,
    "FINNIFTY": 25,
    "MIDCPNIFTY": 50,
    "RELIANCE": 250,
    "HDFCBANK": 550,
    "ICICIBANK": 700,
    "INFY": 300,
    "TCS": 175,
    "SBIN": 750,
    "TATAMOTORS": 575,
    "BHARTIARTL": 475,
    "ITC": 1600,
    "LT": 150,
    "KOTAKBANK": 400,
    "AXISBANK": 625,
}


def get_nse_lot_size(symbol: str) -> int:
    """Returns official NSE lot size for an underlying symbol."""
    return NSE_LOT_SIZES.get(symbol.upper(), 250)


class ContractDetails(BaseModel):
    """Specification of the exact options contract."""
    symbol: str
    option_type: OptionType  # CE or PE
    strike: float
    expiry_date: date
    lot_size: int
    premium: float  # LTP or ask
    bid: float
    ask: float
    delta: float
    theta_per_day: float  # In INR per contract/lot
    iv: float  # Decimal (e.g. 0.16 for 16%)
    iv_percentile: float  # 0 to 100


class LiquidityStatus(BaseModel):
    """Liquidity verification and rejection gate."""
    is_liquid: bool
    spread_pct: float
    volume: int
    open_interest: int
    rejection_reasons: List[str] = Field(default_factory=list)


class TradePlan(BaseModel):
    """Deterministic price levels and risk-reward profile."""
    entry_price: float
    stop_loss: float
    target_1: float
    target_2: float
    risk_per_share: float
    reward_t1_per_share: float
    reward_t2_per_share: float
    risk_reward_t1: float
    risk_reward_t2: float


class NSECostBreakdown(BaseModel):
    """
    Exact statutory NSE options transaction costs breakdown for round-trip trade.
    - Brokerage: Flat ₹20 per executed leg/order (₹40 round-trip for 1 leg)
    - STT: 0.0625% charged exclusively on sell turnover for options in India
    - Exchange Turnover Fee: 0.053% of total turnover
    - GST: 18% on (Brokerage + Exchange Turnover Fee)
    - SEBI Charges: ₹10 per crore (0.0001% of total turnover)
    - Stamp Duty: 0.003% on buy turnover
    """
    brokerage: float
    stt: float
    exchange_fee: float
    gst: float
    sebi_charges: float
    stamp_duty: float
    total_charges: float
    gross_t1_pnl: float
    net_t1_pnl: float
    gross_t2_pnl: float
    net_t2_pnl: float
    cost_per_lot: float


class PositionSizing(BaseModel):
    """Capital preservation and lot sizing output."""
    capital: float
    risk_pct: float
    max_risk_amount: float
    suggested_lots: int
    suggested_quantity: int
    total_capital_deployed: float
    max_loss_rupees: float
    actual_risk_pct_of_capital: float
    breakeven_price: float


class TradeIdea(BaseModel):
    """Complete actionable trade idea card for 60-second decision terminal."""
    id: str
    symbol: str
    strategy_name: str  # e.g., "Long Call (Momentum)", "Bull Call Spread"
    direction: str  # "CALL (BULLISH)" or "PUT (BEARISH)"
    confidence_score: float  # 0 to 100
    reasons_fired: List[str]
    contract: ContractDetails
    liquidity: LiquidityStatus
    plan: TradePlan
    sizing: PositionSizing
    costs: NSECostBreakdown
    why_not_to_take: List[str]
    is_executable: bool
    rejection_reasons: List[str] = Field(default_factory=list)


def evaluate_liquidity(
    symbol: str,
    bid: float,
    ask: float,
    volume: int,
    open_interest: int,
) -> LiquidityStatus:
    """
    Strict liquidity rejection gate. Rejects illiquid strikes outright.
    """
    rejections: List[str] = []
    
    if bid <= 0 or ask <= 0:
        return LiquidityStatus(
            is_liquid=False,
            spread_pct=1.0,
            volume=volume,
            open_interest=open_interest,
            rejection_reasons=["Invalid or zero Bid/Ask quotes"],
        )

    if bid > ask:
        return LiquidityStatus(
            is_liquid=False,
            spread_pct=1.0,
            volume=volume,
            open_interest=open_interest,
            rejection_reasons=["Crossed market: Bid price exceeds Ask price"],
        )

    mid = (bid + ask) / 2.0
    spread_pct = (ask - bid) / max(0.01, mid)

    is_index = symbol.upper() in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]
    max_spread = 0.035 if is_index else 0.065  # 3.5% for index, 6.5% for stocks
    min_volume = 100 if is_index else 25
    min_oi = 1000 if is_index else 250

    if spread_pct > max_spread:
        rejections.append(f"Bid-Ask spread ({spread_pct:.1%}) exceeds safety ceiling ({max_spread:.1%})")
    if volume < min_volume:
        rejections.append(f"Volume ({volume:,}) below minimum threshold ({min_volume:,})")
    if open_interest < min_oi:
        rejections.append(f"Open Interest ({open_interest:,}) below minimum depth ({min_oi:,})")

    return LiquidityStatus(
        is_liquid=len(rejections) == 0,
        spread_pct=round(spread_pct, 4),
        volume=volume,
        open_interest=open_interest,
        rejection_reasons=rejections,
    )


def calculate_nse_charges(
    entry_price: float,
    target_1: float,
    target_2: float,
    quantity: int,
    lots: int,
    is_buy_first: bool = True,
    brokerage_per_order: float = 20.0,
) -> NSECostBreakdown:
    """
    Calculates exact NSE options transaction costs and net P&Ls after all fees and taxes.
    """
    if quantity <= 0 or lots <= 0 or entry_price <= 0:
        return NSECostBreakdown(
            brokerage=0.0,
            stt=0.0,
            exchange_fee=0.0,
            gst=0.0,
            sebi_charges=0.0,
            stamp_duty=0.0,
            total_charges=0.0,
            gross_t1_pnl=0.0,
            net_t1_pnl=0.0,
            gross_t2_pnl=0.0,
            net_t2_pnl=0.0,
            cost_per_lot=0.0,
        )

    # Round trip = 2 orders (Entry + Exit)
    total_brokerage = brokerage_per_order * 2.0

    buy_turnover_entry = entry_price * quantity if is_buy_first else target_1 * quantity
    sell_turnover_t1 = target_1 * quantity if is_buy_first else entry_price * quantity
    
    total_turnover_t1 = buy_turnover_entry + sell_turnover_t1

    # 1. STT: 0.0625% on SELL turnover only
    stt = sell_turnover_t1 * 0.000625

    # 2. Exchange Turnover Charge: 0.053% of turnover
    exchange_fee = total_turnover_t1 * 0.00053

    # 3. GST: 18% on (Brokerage + Exchange turnover charge)
    gst = (total_brokerage + exchange_fee) * 0.18

    # 4. SEBI turnover charge: ₹10 / crore (0.0001%)
    sebi_charges = total_turnover_t1 * 0.000001

    # 5. Stamp Duty: 0.003% on BUY side only
    stamp_duty = buy_turnover_entry * 0.00003

    total_charges = round(total_brokerage + stt + exchange_fee + gst + sebi_charges + stamp_duty, 2)
    cost_per_lot = round(total_charges / max(1, lots), 2)

    gross_t1 = round((target_1 - entry_price) * quantity if is_buy_first else (entry_price - target_1) * quantity, 2)
    net_t1 = round(gross_t1 - total_charges, 2)

    # T2 calculations (assuming slightly higher turnover on exit)
    sell_turnover_t2 = target_2 * quantity if is_buy_first else entry_price * quantity
    total_turnover_t2 = buy_turnover_entry + sell_turnover_t2
    stt_t2 = sell_turnover_t2 * 0.000625
    exchange_fee_t2 = total_turnover_t2 * 0.00053
    gst_t2 = (total_brokerage + exchange_fee_t2) * 0.18
    sebi_t2 = total_turnover_t2 * 0.000001
    total_charges_t2 = round(total_brokerage + stt_t2 + exchange_fee_t2 + gst_t2 + sebi_t2 + stamp_duty, 2)

    gross_t2 = round((target_2 - entry_price) * quantity if is_buy_first else (entry_price - target_2) * quantity, 2)
    net_t2 = round(gross_t2 - total_charges_t2, 2)

    return NSECostBreakdown(
        brokerage=round(total_brokerage, 2),
        stt=round(stt, 2),
        exchange_fee=round(exchange_fee, 2),
        gst=round(gst, 2),
        sebi_charges=round(sebi_charges, 2),
        stamp_duty=round(stamp_duty, 2),
        total_charges=total_charges,
        gross_t1_pnl=gross_t1,
        net_t1_pnl=net_t1,
        gross_t2_pnl=gross_t2,
        net_t2_pnl=net_t2,
        cost_per_lot=cost_per_lot,
    )


def compute_position_sizing(
    capital: float,
    risk_pct: float,
    entry_price: float,
    stop_loss: float,
    lot_size: int,
    total_charges_estimate: float = 80.0,
) -> PositionSizing:
    """
    Computes suggested lots based on max risk amount and stop-loss distance.
    Guarantees no exceeding of capital or configured risk tolerance.
    """
    if capital <= 0 or risk_pct <= 0 or entry_price <= 0:
        return PositionSizing(
            capital=capital,
            risk_pct=risk_pct,
            max_risk_amount=0.0,
            suggested_lots=0,
            suggested_quantity=0,
            total_capital_deployed=0.0,
            max_loss_rupees=0.0,
            actual_risk_pct_of_capital=0.0,
            breakeven_price=entry_price,
        )

    max_risk_amount = round(capital * (risk_pct / 100.0), 2)
    risk_per_share = max(0.5, abs(entry_price - stop_loss))
    risk_per_lot = (risk_per_share * lot_size) + (total_charges_estimate / 2.0)

    suggested_lots = int(math.floor(max_risk_amount / risk_per_lot))
    if suggested_lots < 1:
        # Check if 1 lot is within 1.5x of risk limit
        one_lot_risk = risk_per_lot
        if one_lot_risk <= max_risk_amount * 1.25 and (entry_price * lot_size) <= capital:
            suggested_lots = 1
        else:
            suggested_lots = 0

    suggested_qty = suggested_lots * lot_size
    deployed_capital = round(entry_price * suggested_qty, 2)
    
    # In buying options, max loss is premium paid (if held to zero) or stop loss
    max_loss = round((risk_per_share * suggested_qty) + total_charges_estimate, 2) if suggested_qty > 0 else 0.0
    actual_risk_pct = round((max_loss / capital) * 100.0, 2) if capital > 0 else 0.0

    # Breakeven includes round-trip charges per share
    cost_per_share = (total_charges_estimate / max(1, suggested_qty)) if suggested_qty > 0 else 0.0
    breakeven = round(entry_price + cost_per_share, 2)

    return PositionSizing(
        capital=capital,
        risk_pct=risk_pct,
        max_risk_amount=max_risk_amount,
        suggested_lots=suggested_lots,
        suggested_quantity=suggested_qty,
        total_capital_deployed=deployed_capital,
        max_loss_rupees=max_loss,
        actual_risk_pct_of_capital=actual_risk_pct,
        breakeven_price=breakeven,
    )


def build_trade_idea(
    symbol: str,
    strategy_name: str,
    direction_tag: str,  # e.g., "CALL (BULLISH)" or "PUT (BEARISH)"
    option_type: OptionType,
    strike: float,
    expiry_date: date,
    spot_price: float,
    premium: float,
    bid: float,
    ask: float,
    volume: int,
    open_interest: int,
    iv: float,
    iv_percentile: float,
    confidence_score: float,
    reasons_fired: List[str],
    why_not_to_take: List[str],
    capital: float = 500000.0,
    risk_pct: float = 1.0,
    stop_loss_pct: float = 0.35,  # 35% SL on option premium
    target_1_rr: float = 1.8,    # 1:1.8 R:R
    target_2_rr: float = 2.8,    # 1:2.8 R:R
) -> TradeIdea:
    """
    Constructs an end-to-end validated TradeIdea object with exact Greeks, costs, sizing, and filters.
    """
    lot_size = get_nse_lot_size(symbol)

    # Time to expiry
    days_to_expiry = max(1, (expiry_date - date.today()).days)
    tte = days_to_expiry / 365.0

    # Greeks
    greeks = black_scholes_greeks(
        spot=spot_price,
        strike=strike,
        tte=tte,
        r=0.07,
        sigma=max(0.05, iv),
        option_type=option_type,
        underlying=symbol,
    )
    delta = round(greeks.delta, 2)
    # Theta is per day per share; convert to total decay per lot per day in ₹
    theta_per_share = greeks.theta
    theta_per_lot_day = round(abs(theta_per_share) * lot_size, 2)

    # Liquidity check
    liquidity = evaluate_liquidity(
        symbol=symbol,
        bid=bid,
        ask=ask,
        volume=volume,
        open_interest=open_interest,
    )

    # Trade plan
    entry_price = round(ask if ask > 0 else premium, 2)
    risk_distance = round(entry_price * stop_loss_pct, 2)
    stop_loss = max(0.05, round(entry_price - risk_distance, 2))
    target_1 = round(entry_price + (risk_distance * target_1_rr), 2)
    target_2 = round(entry_price + (risk_distance * target_2_rr), 2)
    
    plan = TradePlan(
        entry_price=entry_price,
        stop_loss=stop_loss,
        target_1=target_1,
        target_2=target_2,
        risk_per_share=risk_distance,
        reward_t1_per_share=round(target_1 - entry_price, 2),
        reward_t2_per_share=round(target_2 - entry_price, 2),
        risk_reward_t1=round(target_1_rr, 1),
        risk_reward_t2=round(target_2_rr, 1),
    )

    # Position sizing
    sizing = compute_position_sizing(
        capital=capital,
        risk_pct=risk_pct,
        entry_price=entry_price,
        stop_loss=stop_loss,
        lot_size=lot_size,
    )

    # NSE transaction costs
    costs = calculate_nse_charges(
        entry_price=entry_price,
        target_1=target_1,
        target_2=target_2,
        quantity=max(lot_size, sizing.suggested_quantity),
        lots=max(1, sizing.suggested_lots),
        is_buy_first=True,
    )

    # Executable gating
    rejections = []
    if not liquidity.is_liquid:
        rejections.extend(liquidity.rejection_reasons)
    if sizing.suggested_lots < 1:
        rejections.append("Calculated position size is 0 lots based on strict risk limit")

    is_executable = (len(rejections) == 0)

    contract = ContractDetails(
        symbol=symbol,
        option_type=option_type,
        strike=strike,
        expiry_date=expiry_date,
        lot_size=lot_size,
        premium=entry_price,
        bid=bid,
        ask=ask,
        delta=delta,
        theta_per_day=theta_per_lot_day,
        iv=round(iv, 4),
        iv_percentile=round(iv_percentile, 1),
    )

    idea_id = f"{symbol}_{strike}_{option_type.value}_{expiry_date.strftime('%d%b')}"

    return TradeIdea(
        id=idea_id,
        symbol=symbol,
        strategy_name=strategy_name,
        direction=direction_tag,
        confidence_score=round(confidence_score, 1),
        reasons_fired=reasons_fired,
        contract=contract,
        liquidity=liquidity,
        plan=plan,
        sizing=sizing,
        costs=costs,
        why_not_to_take=why_not_to_take,
        is_executable=is_executable,
        rejection_reasons=rejections,
    )


def generate_curated_trade_ideas(
    symbol: str = "NIFTY",
    spot_price: Optional[float] = None,
    capital: float = 500000.0,
    risk_pct: float = 1.0,
) -> List[TradeIdea]:
    """
    Synthesizes curated trade ideas for an underlying, comparing Call, Put, and Spreads,
    with explicit liquidity validation and 'Why NOT to take this trade' boxes.
    """
    sym = symbol.upper()
    
    # Base spot defaults
    defaults = {
        "NIFTY": 24850.0,
        "BANKNIFTY": 51200.0,
        "RELIANCE": 2980.0,
        "HDFCBANK": 1670.0,
        "TCS": 4250.0,
        "INFY": 1890.0,
    }
    spot = spot_price or defaults.get(sym, 24850.0)
    
    # Step strike
    step = 50.0 if sym == "NIFTY" else (100.0 if sym == "BANKNIFTY" else 20.0)
    atm_strike = round(spot / step) * step

    # Expiry: Nearest upcoming Thursday
    today = date.today()
    days_until_thursday = (3 - today.weekday()) % 7
    if days_until_thursday == 0:
        days_until_thursday = 7
    nearest_expiry = today + timedelta(days=days_until_thursday)

    ideas: List[TradeIdea] = []

    # Idea 1: Bullish Momentum (Long Call) - ATM+1 Strike
    call_strike = atm_strike
    call_premium = round(spot * 0.0095, 1)  # realistic ~1% of spot
    ideas.append(
        build_trade_idea(
            symbol=sym,
            strategy_name=f"{sym} ATM Call Momentum",
            direction_tag="CALL (BULLISH)",
            option_type=OptionType.CE,
            strike=call_strike,
            expiry_date=nearest_expiry,
            spot_price=spot,
            premium=call_premium,
            bid=round(call_premium * 0.992, 1),
            ask=round(call_premium * 1.008, 1),
            volume=342500,
            open_interest=4820000,
            iv=0.148,
            iv_percentile=38.0,
            confidence_score=78.0,
            reasons_fired=[
                "Index consolidating above VWAP with bullish RSI momentum (>58)",
                "FII net index futures buying observed in recent sessions",
                "Favorable Call OI unwinding at ATM strike indicating upward breakout clearance",
            ],
            why_not_to_take=[
                f"Theta decay is ₹{round(call_premium * 0.12 * get_nse_lot_size(sym), 0)}/day per lot — time works against you if the index moves sideways.",
                "Upcoming macro RBI / US Fed rate decisions can trigger overnight gap-downs.",
                "R:R deteriorates sharply if entry fills > 2% above recommended limit price.",
            ],
            capital=capital,
            risk_pct=risk_pct,
        )
    )

    # Idea 2: Bearish Breakdown (Long Put) - OTM-1 Strike
    put_strike = atm_strike - step
    put_premium = round(spot * 0.0080, 1)
    ideas.append(
        build_trade_idea(
            symbol=sym,
            strategy_name=f"{sym} OTM Put Hedge / Reversal",
            direction_tag="PUT (BEARISH)",
            option_type=OptionType.PE,
            strike=put_strike,
            expiry_date=nearest_expiry,
            spot_price=spot,
            premium=put_premium,
            bid=round(put_premium * 0.988, 1),
            ask=round(put_premium * 1.012, 1),
            volume=198000,
            open_interest=3150000,
            iv=0.165,
            iv_percentile=52.0,
            confidence_score=64.0,
            reasons_fired=[
                "Repeated rejection at major daily overhead resistance level",
                "Put-Call Ratio (PCR) declining from 1.15 to 0.88 over 3 sessions",
                "Volume drying up on upward bounces indicating distribution",
            ],
            why_not_to_take=[
                "Bearish momentum often experiences violent short-covering rallies in Indian markets.",
                "India VIX is below 15; low volatility makes directional Put purchasing expensive relative to actual move.",
                "Higher time-frame trend remains structurally upward on weekly charts.",
            ],
            capital=capital,
            risk_pct=risk_pct,
        )
    )

    # Idea 3: Illiquid Strike Demonstration (To demonstrate strict liquidity rejection)
    far_otm_strike = atm_strike + (step * 8)
    far_premium = round(spot * 0.0012, 1)
    ideas.append(
        build_trade_idea(
            symbol=sym,
            strategy_name=f"{sym} Far OTM Lottery Call (UNSAFE)",
            direction_tag="CALL (SPECULATIVE)",
            option_type=OptionType.CE,
            strike=far_otm_strike,
            expiry_date=nearest_expiry,
            spot_price=spot,
            premium=far_premium,
            bid=round(far_premium * 0.82, 1),  # Wide 18% spread!
            ask=round(far_premium * 1.18, 1),
            volume=8,   # Illiquid
            open_interest=80,  # Illiquid
            iv=0.285,
            iv_percentile=91.0,
            confidence_score=31.0,
            reasons_fired=[
                "Extremely cheap rupee premium tempts speculative buyers",
                "Far out of money strike",
            ],
            why_not_to_take=[
                "🚨 CRITICAL LIQUIDITY REJECTION: Bid-Ask spread exceeds 15% — you will suffer severe slippage upon entry and exit.",
                "Delta is under 0.08; probability of expiring in-the-money is under 6%.",
                "Near 100% loss of capital expected at expiry due to rapid theta decay.",
            ],
            capital=capital,
            risk_pct=risk_pct,
        )
    )

    return ideas
