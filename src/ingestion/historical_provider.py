"""
Concrete Historical Options Data Providers.

Supports:
- DatabaseHistoricalOptionsProvider: Queries loaded DB quotes in point-in-time sequence.
- CSVHistoricalOptionsProvider: Parses historical CSV/Parquet archives and populates DB on demand.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List, Optional
import pandas as pd
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from src.database.connection import get_session
from src.database.models import OptionsContractDB, OptionsQuoteDB, EquityPriceDB
from src.ingestion.schemas import DataQualityStatus, OptionChainSnapshot, OptionQuote, OptionType
from src.ingestion.historical_base import HistoricalDataQualityReport, HistoricalOptionsDataProvider
from src.ingestion.pipeline import HistoricalDataIngestionPipeline


class DatabaseHistoricalOptionsProvider(HistoricalOptionsDataProvider):
    """
    Provider backed by SQLite/PostgreSQL database tables (options_contracts, options_quotes).
    Enforces strict point-in-time isolation (only timestamp <= T).
    """

    def __init__(self, db_session: Optional[Session] = None):
        self._db_session = db_session

    @property
    def provider_name(self) -> str:
        return "DATABASE_HISTORICAL_PROVIDER"

    def load_historical_quotes(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> List[OptionQuote]:
        session = self._db_session if self._db_session else get_session()
        should_close = self._db_session is None

        try:
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())

            stmt = (
                select(OptionsQuoteDB, OptionsContractDB)
                .join(OptionsContractDB, OptionsQuoteDB.contract_id == OptionsContractDB.id)
                .where(
                    and_(
                        OptionsContractDB.underlying == symbol.upper(),
                        OptionsQuoteDB.timestamp >= start_dt,
                        OptionsQuoteDB.timestamp <= end_dt,
                    )
                )
                .order_by(OptionsQuoteDB.timestamp.asc())
            )

            results = session.execute(stmt).all()
            quotes: List[OptionQuote] = []

            for q_db, c_db in results:
                opt_type = OptionType.CE if c_db.option_type == "CE" else OptionType.PE
                quote = OptionQuote(
                    contract_symbol=c_db.contract_symbol or f"{c_db.underlying}{c_db.strike_price}{c_db.option_type}",
                    underlying=c_db.underlying,
                    option_type=opt_type,
                    strike_price=c_db.strike_price,
                    expiry_date=c_db.expiry_date,
                    timestamp=q_db.timestamp,
                    last_price=q_db.last_price,
                    bid_price=q_db.bid_price,
                    ask_price=q_db.ask_price,
                    volume=q_db.volume,
                    open_interest=q_db.open_interest,
                    source=q_db.source,
                    data_quality=DataQualityStatus.GOOD if q_db.data_quality == "GOOD" else DataQualityStatus.PARTIAL,
                )
                quotes.append(quote)

            return quotes
        finally:
            if should_close:
                session.close()

    def get_historical_chain_snapshot(
        self,
        symbol: str,
        timestamp: datetime,
    ) -> Optional[OptionChainSnapshot]:
        session = self._db_session if self._db_session else get_session()
        should_close = self._db_session is None

        try:
            stmt = (
                select(OptionsQuoteDB, OptionsContractDB)
                .join(OptionsContractDB, OptionsQuoteDB.contract_id == OptionsContractDB.id)
                .where(
                    and_(
                        OptionsContractDB.underlying == symbol.upper(),
                        OptionsQuoteDB.timestamp == timestamp,
                    )
                )
            )

            results = session.execute(stmt).all()
            if not results:
                return None

            from src.ingestion.schemas import OptionStrikeRow

            strikes_dict: Dict[float, OptionStrikeRow] = {}
            expiry_date: Optional[date] = None

            for q_db, c_db in results:
                if expiry_date is None:
                    expiry_date = c_db.expiry_date

                opt_type = OptionType.CE if c_db.option_type == "CE" else OptionType.PE
                contract_symbol = c_db.contract_symbol or f"{c_db.underlying}{int(c_db.strike_price)}{c_db.option_type}"
                
                quote = OptionQuote(
                    contract_symbol=contract_symbol,
                    underlying=c_db.underlying,
                    option_type=opt_type,
                    strike_price=c_db.strike_price,
                    expiry_date=c_db.expiry_date,
                    timestamp=q_db.timestamp,
                    last_price=q_db.last_price,
                    bid_price=q_db.bid_price,
                    ask_price=q_db.ask_price,
                    volume=q_db.volume,
                    open_interest=q_db.open_interest,
                    source=q_db.source,
                    data_quality=DataQualityStatus.GOOD if q_db.data_quality == "GOOD" else DataQualityStatus.PARTIAL,
                )

                if c_db.strike_price not in strikes_dict:
                    strikes_dict[c_db.strike_price] = OptionStrikeRow(
                        strike_price=c_db.strike_price,
                        expiry_date=c_db.expiry_date,
                    )

                if opt_type == OptionType.CE:
                    strikes_dict[c_db.strike_price].ce = quote
                else:
                    strikes_dict[c_db.strike_price].pe = quote

            # Spot price lookup from EquityPriceDB at timestamp date
            spot_stmt = select(EquityPriceDB.close).where(
                and_(
                    EquityPriceDB.symbol == symbol.upper(),
                    EquityPriceDB.date == timestamp.date(),
                )
            )
            spot_price = session.execute(spot_stmt).scalar() or 24000.0

            return OptionChainSnapshot(
                underlying=symbol.upper(),
                spot_price=spot_price,
                timestamp=timestamp,
                expiry_date=expiry_date or timestamp.date(),
                strikes=list(strikes_dict.values()),
                source=self.provider_name,
                data_quality=DataQualityStatus.GOOD,
            )
        finally:
            if should_close:
                session.close()

    def audit_dataset_quality(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> HistoricalDataQualityReport:
        session = self._db_session if self._db_session else get_session()
        should_close = self._db_session is None

        try:
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())

            stmt = (
                select(OptionsQuoteDB, OptionsContractDB)
                .join(OptionsContractDB, OptionsQuoteDB.contract_id == OptionsContractDB.id)
                .where(
                    and_(
                        OptionsContractDB.underlying == symbol.upper(),
                        OptionsQuoteDB.timestamp >= start_dt,
                        OptionsQuoteDB.timestamp <= end_dt,
                    )
                )
            )

            results = session.execute(stmt).all()
            total_records = len(results)

            if total_records == 0:
                return HistoricalDataQualityReport(
                    symbol=symbol,
                    data_source=self.provider_name,
                    granularity="UNKNOWN",
                    start_date=start_date,
                    end_date=end_date,
                    is_suitable_for_backtesting=False,
                    audit_notes=["No historical quote records found in database."],
                )

            missing_ltp = sum(1 for q, c in results if q.last_price is None)
            missing_bid_ask = sum(1 for q, c in results if q.bid_price is None or q.ask_price is None)
            missing_oi = sum(1 for q, c in results if q.open_interest is None)
            missing_vol = sum(1 for q, c in results if q.volume is None)

            unique_expiries = len(set(c.expiry_date for q, c in results))
            unique_strikes = len(set(c.strike_price for q, c in results))
            unique_contracts = len(set(c.id for q, c in results))

            missing_ltp_pct = round(missing_ltp / total_records, 4)
            missing_bid_ask_pct = round(missing_bid_ask / total_records, 4)
            missing_oi_pct = round(missing_oi / total_records, 4)
            missing_vol_pct = round(missing_vol / total_records, 4)

            is_suitable = total_records >= 100 and missing_ltp_pct < 0.05

            notes = []
            if missing_bid_ask_pct > 0.5:
                notes.append("Over 50% quotes lack bid/ask spreads. Backtest will fall back to slippage-adjusted LTP.")
            if missing_oi_pct > 0.5:
                notes.append("Open Interest sparse in dataset.")

            return HistoricalDataQualityReport(
                symbol=symbol,
                data_source=self.provider_name,
                granularity="EOD/INTRADAY",
                start_date=start_date,
                end_date=end_date,
                total_quote_records=total_records,
                total_contracts_count=unique_contracts,
                unique_expiries_count=unique_expiries,
                unique_strikes_count=unique_strikes,
                missing_ltp_pct=missing_ltp_pct,
                missing_bid_ask_pct=missing_bid_ask_pct,
                missing_oi_pct=missing_oi_pct,
                missing_volume_pct=missing_vol_pct,
                is_suitable_for_backtesting=is_suitable,
                audit_notes=notes,
            )
        finally:
            if should_close:
                session.close()


class CSVHistoricalOptionsProvider(DatabaseHistoricalOptionsProvider):
    """
    CSV File archive historical options provider.
    Parses CSV/Parquet archives, executes HistoricalDataIngestionPipeline, and delegates querying to DB.
    """

    def __init__(self, csv_filepath: str, db_session: Optional[Session] = None):
        super().__init__(db_session=db_session)
        self.csv_filepath = csv_filepath
        self.pipeline = HistoricalDataIngestionPipeline(db_session=db_session)

    @property
    def provider_name(self) -> str:
        return f"CSV_ARCHIVE ({self.csv_filepath})"

    def ingest_csv_file(self) -> int:
        """
        Parses CSV and populates database tables.
        """
        df = pd.read_csv(self.csv_filepath)
        stats = self.pipeline.ingest_quotes_dataframe(df, source_name=self.provider_name)
        return stats.quotes_inserted
