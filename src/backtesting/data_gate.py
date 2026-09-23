"""
Data Availability Gate for Options Backtesting.

MANDATORY DATA AVAILABILITY GATE:
Before running a backtest, inspect the database / provider for genuine historical options quotes.
If genuine historical options data is unavailable or insufficient:
DO NOT: fabricate it, use today's chain, generate synthetic data presented as historical, quietly substitute theoretical prices.
Instead report: "HISTORICAL OPTIONS DATA INSUFFICIENT FOR VALID BACKTEST".
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from src.database.connection import get_session
from src.database.models import OptionsContractDB, OptionsQuoteDB, EquityPriceDB


class DataAvailabilityStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    SYNTHETIC_ONLY = "SYNTHETIC_ONLY"


class DataAvailabilityReport(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    status: DataAvailabilityStatus
    message: str
    equity_bars_count: int = 0
    option_contracts_count: int = 0
    option_quotes_count: int = 0
    missing_elements: List[str] = Field(default_factory=list)
    recommendation: str = ""
    is_synthetic_allowed_for_testing: bool = True


class DataGate:
    """
    Validates whether required historical options and underlying price records exist.
    """

    def __init__(self, db_session: Optional[Session] = None):
        self._db_session = db_session

    def evaluate_availability(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        min_option_quotes: int = 100,
    ) -> DataAvailabilityReport:
        """
        Check database records for symbol and date range.
        """
        symbol_upper = symbol.upper()
        missing: List[str] = []

        # If no DB session provided, fetch one
        if self._db_session:
            return self._evaluate_with_session(
                self._db_session, symbol_upper, start_date, end_date, min_option_quotes
            )
        
        session = get_session()
        try:
            return self._evaluate_with_session(
                session, symbol_upper, start_date, end_date, min_option_quotes
            )
        finally:
            session.close()

    def _evaluate_with_session(
        self,
        session: Session,
        symbol: str,
        start_date: date,
        end_date: date,
        min_option_quotes: int,
    ) -> DataAvailabilityReport:
        missing: List[str] = []

        # 1. Equity price history count
        equity_stmt = select(func.count(EquityPriceDB.id)).where(
            and_(
                EquityPriceDB.symbol == symbol,
                EquityPriceDB.date >= start_date,
                EquityPriceDB.date <= end_date,
            )
        )
        equity_count = session.execute(equity_stmt).scalar() or 0

        if equity_count == 0:
            missing.append(f"No equity price history found for {symbol} between {start_date} and {end_date}.")

        # 2. Options contracts count
        contracts_stmt = select(func.count(OptionsContractDB.id)).where(
            OptionsContractDB.underlying == symbol
        )
        contracts_count = session.execute(contracts_stmt).scalar() or 0

        if contracts_count == 0:
            missing.append(f"No options contracts registered for {symbol}.")

        # 3. Options quotes count within date range
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        quotes_stmt = (
            select(func.count(OptionsQuoteDB.id))
            .join(OptionsContractDB, OptionsQuoteDB.contract_id == OptionsContractDB.id)
            .where(
                and_(
                    OptionsContractDB.underlying == symbol,
                    OptionsQuoteDB.timestamp >= start_dt,
                    OptionsQuoteDB.timestamp <= end_dt,
                )
            )
        )
        quotes_count = session.execute(quotes_stmt).scalar() or 0

        if quotes_count < min_option_quotes:
            missing.append(
                f"Options quote observations count ({quotes_count}) is below minimum requirement ({min_option_quotes})."
            )

        # Status determination
        if len(missing) == 0 and quotes_count >= min_option_quotes:
            status = DataAvailabilityStatus.AVAILABLE
            msg = f"Historical data for {symbol} is fully available ({quotes_count} option quotes, {equity_count} equity bars)."
            rec = "Proceed with genuine backtest."
        elif equity_count > 0 and quotes_count > 0:
            status = DataAvailabilityStatus.PARTIAL
            msg = f"PARTIAL historical options data available ({quotes_count} quotes). Backtest may have gaps."
            rec = "Historical options data incomplete. Results will be marked PARTIAL."
        else:
            status = DataAvailabilityStatus.UNAVAILABLE
            msg = "HISTORICAL OPTIONS DATA INSUFFICIENT FOR VALID BACKTEST"
            rec = (
                "Free data sources (yfinance/NSE direct) do not store historical multi-strike option chain time series. "
                "To backtest historical options strategies, configure a historical broker dataset (e.g. Dhan / Kite Connect / GDFL). "
                "Synthetic test data may be used solely for software testing."
            )

        return DataAvailabilityReport(
            symbol=symbol,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            status=status,
            message=msg,
            equity_bars_count=equity_count,
            option_contracts_count=contracts_count,
            option_quotes_count=quotes_count,
            missing_elements=missing,
            recommendation=rec,
            is_synthetic_allowed_for_testing=True,
        )
