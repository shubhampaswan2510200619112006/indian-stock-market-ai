"""
Synthetic Fixture Generator for Unit & Integration Testing of the Backtest Engine.

MANDATORY RULE:
Synthetic data may ONLY be used for software/unit testing of the backtest engine itself.
All outputs generated using synthetic data MUST be unmistakably labeled "SYNTHETIC TEST DATA — SOFTWARE TESTING ONLY".
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple
import numpy as np

from src.ingestion.schemas import DataQualityStatus, OptionChainSnapshot, OptionQuote, OptionType
from src.options.pricing import black_scholes_greeks, black_scholes_price


def generate_synthetic_option_history(
    underlying: str = "NIFTY",
    start_date: date = date(2026, 1, 1),
    num_days: int = 30,
    initial_spot: float = 24000.0,
    daily_vol: float = 0.01,
    iv_annual: float = 0.15,
    risk_free_rate: float = 0.07,
    strike_step: float = 100.0,
    strike_count: int = 11,
    lot_size: int = 25,
) -> List[Tuple[datetime, float, OptionChainSnapshot]]:
    """
    Generates a deterministic synthetic time series of spot prices and option chain snapshots.
    Used STRICTLY for testing the chronological execution engine, position sizing, metrics, and walk-forward logic.
    """
    np.random.seed(42)  # Deterministic seed for reproducible testing
    
    current_spot = initial_spot
    snapshots: List[Tuple[datetime, float, OptionChainSnapshot]] = []
    
    # Expiry 45 days from start
    expiry_date = start_date + timedelta(days=45)
    
    for day_idx in range(num_days):
        current_date = start_date + timedelta(days=day_idx)
        # Skip weekends
        if current_date.weekday() >= 5:
            continue
            
        timestamp = datetime.combine(current_date, datetime.min.time().replace(hour=15, minute=30))
        
        # Spot random walk
        if day_idx > 0:
            return_val = np.random.normal(0.0003, daily_vol)
            current_spot = round(current_spot * (1.0 + return_val), 2)
            
        dte_years = max((expiry_date - current_date).days / 365.0, 0.001)
        
        # Center strikes around initial spot
        atm_center = round(initial_spot / strike_step) * strike_step
        half_strikes = strike_count // 2
        strikes = [atm_center + i * strike_step for i in range(-half_strikes, half_strikes + 1)]
        
        quotes: Dict[str, OptionQuote] = {}
        
        for strike in strikes:
            for opt_type in [OptionType.CE, OptionType.PE]:
                # Theoretical BS price
                bs_price = black_scholes_price(
                    spot=current_spot,
                    strike=strike,
                    tte=dte_years,
                    r=risk_free_rate,
                    sigma=iv_annual,
                    option_type=opt_type,
                )
                
                # Synthetic bid/ask with 2% spread
                spread = max(0.5, bs_price * 0.02)
                bid = max(0.05, round(bs_price - spread / 2.0, 2))
                ask = max(0.10, round(bs_price + spread / 2.0, 2))
                ltp = round(bs_price, 2)
                
                # Synthetic volume/OI
                dist_from_atm = abs(current_spot - strike)
                oi = int(max(1000, 50000 - dist_from_atm * 50))
                vol = int(max(100, 10000 - dist_from_atm * 10))
                
                contract_symbol = f"{underlying}{expiry_date.strftime('%y%b').upper()}{int(strike)}{opt_type.value}"
                
                quote = OptionQuote(
                    contract_symbol=contract_symbol,
                    underlying=underlying,
                    option_type=opt_type,
                    strike_price=strike,
                    expiry_date=expiry_date,
                    timestamp=timestamp,
                    last_price=ltp,
                    bid_price=bid,
                    ask_price=ask,
                    volume=vol,
                    open_interest=oi,
                    change_in_oi=100,
                    implied_volatility_source=iv_annual,
                    source="SYNTHETIC TEST DATA",
                    data_quality=DataQualityStatus.GOOD,
                )
                quotes[contract_symbol] = quote
                
        chain_snap = OptionChainSnapshot(
            underlying=underlying,
            spot_price=current_spot,
            timestamp=timestamp,
            expiry_date=expiry_date,
            quotes=quotes,
            source="SYNTHETIC TEST DATA",
            data_quality=DataQualityStatus.GOOD,
        )
        
        snapshots.append((timestamp, current_spot, chain_snap))
        
    return snapshots
