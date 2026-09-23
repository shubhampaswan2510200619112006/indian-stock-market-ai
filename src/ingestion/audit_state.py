"""
Current Database State Audit Module.

Inspects:
- options_contracts
- options_quotes
- equity_prices
- underlyings

Reports exact record counts, date ranges, symbols, expiries, strikes, missing-value rates, and backtest readiness.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from src.database.connection import get_session
from src.database.models import OptionsContractDB, OptionsQuoteDB, EquityPriceDB, UnderlyingDB


class DatabaseAuditReport(BaseModel):
    underlyings_count: int = 0
    equity_prices_count: int = 0
    equity_date_range: Optional[str] = None
    options_contracts_count: int = 0
    options_quotes_count: int = 0
    options_date_range: Optional[str] = None
    symbols_available: List[str] = Field(default_factory=list)
    unique_expiries: List[str] = Field(default_factory=list)
    unique_strikes_count: int = 0
    missing_bid_ask_pct: float = 0.0
    missing_oi_pct: float = 0.0
    missing_vol_pct: float = 0.0
    is_usable_for_real_backtest: bool = False
    audit_notes: List[str] = Field(default_factory=list)


def audit_current_database_state(db_session: Optional[Session] = None) -> DatabaseAuditReport:
    session = db_session if db_session else get_session()
    should_close = db_session is None

    try:
        u_count = session.query(UnderlyingDB).count()
        eq_count = session.query(EquityPriceDB).count()
        c_count = session.query(OptionsContractDB).count()
        q_count = session.query(OptionsQuoteDB).count()

        notes: List[str] = []

        # Equity date range
        eq_min = session.query(func.min(EquityPriceDB.date)).scalar()
        eq_max = session.query(func.max(EquityPriceDB.date)).scalar()
        eq_range = f"{eq_min} to {eq_max}" if eq_min and eq_max else "None"

        # Options date range
        q_min = session.query(func.min(OptionsQuoteDB.timestamp)).scalar()
        q_max = session.query(func.max(OptionsQuoteDB.timestamp)).scalar()
        q_range = f"{q_min} to {q_max}" if q_min and q_max else "None"

        # Symbols & expiries
        symbols = [s[0] for s in session.query(OptionsContractDB.underlying).distinct().all()]
        expiries = [str(e[0]) for e in session.query(OptionsContractDB.expiry_date).distinct().all()]
        strikes_count = session.query(OptionsContractDB.strike_price).distinct().count()

        # Missing rates
        if q_count > 0:
            missing_ba = session.query(OptionsQuoteDB).filter(
                (OptionsQuoteDB.bid_price.is_(None)) | (OptionsQuoteDB.ask_price.is_(None))
            ).count()
            missing_oi = session.query(OptionsQuoteDB).filter(OptionsQuoteDB.open_interest.is_(None)).count()
            missing_vol = session.query(OptionsQuoteDB).filter(OptionsQuoteDB.volume.is_(None)).count()

            ba_pct = round(missing_ba / q_count, 4)
            oi_pct = round(missing_oi / q_count, 4)
            vol_pct = round(missing_vol / q_count, 4)
        else:
            ba_pct = 0.0
            oi_pct = 0.0
            vol_pct = 0.0

        is_usable = q_count >= 100 and eq_count >= 10

        if q_count == 0:
            notes.append("Database currently lacks options quote observations.")
        elif q_count < 100:
            notes.append(f"Options quote count ({q_count}) is below minimum threshold (100) for statistical validity.")

        if eq_count == 0:
            notes.append("Database lacks underlying equity price history.")

        return DatabaseAuditReport(
            underlyings_count=u_count,
            equity_prices_count=eq_count,
            equity_date_range=eq_range,
            options_contracts_count=c_count,
            options_quotes_count=q_count,
            options_date_range=q_range,
            symbols_available=symbols,
            unique_expiries=expiries,
            unique_strikes_count=strikes_count,
            missing_bid_ask_pct=ba_pct,
            missing_oi_pct=oi_pct,
            missing_vol_pct=vol_pct,
            is_usable_for_real_backtest=is_usable,
            audit_notes=notes,
        )
    finally:
        if should_close:
            session.close()
