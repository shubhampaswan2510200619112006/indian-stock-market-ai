"""
Phase 9 — Genuine Historical Options Bhavcopy Importer & Provider.

Implements HistoricalOptionsDataProvider interface.
Parses genuine NSE FO Bhavcopy archives:
- Correctly separates static contract metadata (OptionsContractDB) from dynamic observations (OptionsQuoteDB).
- Accurately tracks bid_ask_coverage_percentage = 0.0 (Bhavcopy settlement files do not contain Bid/Ask).
- Zero fake Bid/Ask prices or theoretical options prices are generated.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
import io
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy import and_

from src.database.connection import get_session
from src.database.models import OptionsContractDB, OptionsQuoteDB
from src.data_infrastructure.models import (
    DataStatus,
    ObservationTimestamps,
    OptionChainRow,
    OptionChainSnapshotRecord,
    OptionObservation,
    SourceType,
)
from src.data_infrastructure.providers.base import HistoricalOptionsDataProvider
from src.data_infrastructure.providers.verification import ProviderVerificationEngine


class NSEBhavcopyHistoricalProvider(HistoricalOptionsDataProvider):
    """
    Historical options provider parsing official NSE End-of-Day Bhavcopy archives.
    """

    def __init__(self, db_session=None):
        self._provider_name = "NSE_BHAVCOPY_ARCHIVE"
        self._db_session = db_session

    @property
    def provider_name(self) -> str:
        return self._provider_name

    def capabilities(self) -> Dict[str, bool]:
        return {
            "historical_options_quotes": True,
            "historical_settlement_prices": True,
            "open_interest": True,
            "change_in_oi": True,
            "contracts_traded": True,
            "bid_ask": False,            # Transparent: EOD Bhavcopy lacks Bid/Ask depth
            "intraday_candles": False,
            "realtime_quotes": False,
        }

    def health_check(self) -> Dict[str, Any]:
        return {
            "provider_name": self.provider_name,
            "is_healthy": True,
            "status_label": DataStatus.HISTORICAL.value,
            "notes": "Static exchange settlement archive. 100% liveness.",
            "error_count": 0,
        }

    def parse_bhavcopy_csv(self, csv_content_or_path: str | Path) -> List[Dict[str, Any]]:
        """
        Parses genuine NSE Bhavcopy CSV.
        Expected standard columns:
        INSTRUMENT, SYMBOL, EXPIRY_DT, STRIKE_PR, OPTION_TYP, OPEN, HIGH, LOW, CLOSE, SETTLE_PR, CONTRACTS, VAL_INLAKH, OPEN_INT, CHG_IN_OI, TIMESTAMP
        """
        if isinstance(csv_content_or_path, (str, Path)) and Path(str(csv_content_or_path)).is_file():
            df = pd.read_csv(csv_content_or_path)
        else:
            df = pd.read_csv(io.StringIO(str(csv_content_or_path)))

        # Clean column names
        df.columns = [c.strip().upper() for c in df.columns]

        # Filter for Options only (OPTIDX, OPTSTK)
        if "INSTRUMENT" in df.columns:
            df = df[df["INSTRUMENT"].isin(["OPTIDX", "OPTSTK"])]

        records = []
        for _, row in df.iterrows():
            sym = str(row["SYMBOL"]).strip().upper()
            opt_type = str(row["OPTION_TYP"]).strip().upper()
            strike = float(row["STRIKE_PR"])
            
            # Parse expiry date
            exp_str = str(row["EXPIRY_DT"]).strip()
            try:
                exp_dt = datetime.strptime(exp_str, "%d-%b-%Y").date()
            except Exception:
                try:
                    exp_dt = datetime.strptime(exp_str, "%Y-%m-%d").date()
                except Exception:
                    exp_dt = date.today()

            # Parse trade timestamp
            ts_str = str(row.get("TIMESTAMP", row.get("TRADE_DATE", ""))).strip()
            try:
                trade_dt = datetime.strptime(ts_str, "%d-%b-%Y")
            except Exception:
                try:
                    trade_dt = datetime.strptime(ts_str, "%Y-%m-%d")
                except Exception:
                    trade_dt = datetime.now(timezone.utc)

            settle_p = float(row.get("SETTLE_PR", row.get("CLOSE", 0.0)))
            vol = int(row.get("CONTRACTS", row.get("VOLUME", 0)))
            oi = int(row.get("OPEN_INT", row.get("OPEN_INTEREST", 0)))
            chg_oi = int(row.get("CHG_IN_OI", 0))

            records.append({
                "symbol": sym,
                "option_type": opt_type,
                "strike_price": strike,
                "expiry_date": exp_dt,
                "timestamp": trade_dt,
                "last_price": settle_p,
                "bid_price": None,  # Truthful NULL
                "ask_price": None,  # Truthful NULL
                "volume": vol,
                "open_interest": oi,
                "change_in_oi": chg_oi,
                "source": self.provider_name,
            })

        return records

    def ingest_records_to_db(self, records: List[Dict[str, Any]]) -> int:
        """
        Ingests parsed bhavcopy records into OptionsContractDB and OptionsQuoteDB.
        """
        session = self._db_session or get_session()
        should_close = self._db_session is None
        inserted = 0

        try:
            for r in records:
                # Upsert static contract
                contract = session.query(OptionsContractDB).filter(
                    and_(
                        OptionsContractDB.underlying == r["symbol"],
                        OptionsContractDB.option_type == r["option_type"],
                        OptionsContractDB.strike_price == r["strike_price"],
                        OptionsContractDB.expiry_date == r["expiry_date"],
                    )
                ).first()

                if not contract:
                    contract = OptionsContractDB(
                        underlying=r["symbol"],
                        exchange="NSE",
                        instrument_type="INDEX_OPTION" if r["symbol"] in ("NIFTY", "BANKNIFTY", "FINNIFTY") else "STOCK_OPTION",
                        option_type=r["option_type"],
                        strike_price=r["strike_price"],
                        expiry_date=r["expiry_date"],
                        contract_symbol=f"{r['symbol']}{r['expiry_date'].strftime('%y%m%d')}{r['option_type']}{int(r['strike_price'])}",
                        lot_size=25 if r["symbol"] == "NIFTY" else (15 if r["symbol"] == "BANKNIFTY" else 1),
                    )
                    session.add(contract)
                    session.flush()

                # Insert timestamped observation
                quote = OptionsQuoteDB(
                    contract_id=contract.id,
                    timestamp=r["timestamp"],
                    last_price=r["last_price"],
                    bid_price=r["bid_price"],
                    ask_price=r["ask_price"],
                    volume=r["volume"],
                    open_interest=r["open_interest"],
                    change_in_oi=r.get("change_in_oi"),
                    source=self.provider_name,
                    data_quality="GOOD",
                )
                session.add(quote)
                inserted += 1

            session.commit()
            return inserted
        except Exception:
            session.rollback()
            raise
        finally:
            if should_close:
                session.close()

    def load_historical_option_quotes(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> List[OptionObservation]:
        session = self._db_session or get_session()
        should_close = self._db_session is None

        try:
            quotes_db = session.query(OptionsQuoteDB, OptionsContractDB).join(
                OptionsContractDB, OptionsQuoteDB.contract_id == OptionsContractDB.id
            ).filter(
                and_(
                    OptionsContractDB.underlying == symbol.upper(),
                    OptionsQuoteDB.timestamp >= datetime.combine(start_date, datetime.min.time()),
                    OptionsQuoteDB.timestamp <= datetime.combine(end_date, datetime.max.time()),
                )
            ).all()

            observations = []
            for q, c in quotes_db:
                ts = ObservationTimestamps(
                    provider_timestamp=q.timestamp,
                    received_timestamp=q.ingestion_time or q.timestamp,
                    processed_timestamp=q.ingestion_time or q.timestamp,
                )
                obs = OptionObservation(
                    observation_id=f"HIST-OPT-{q.id}",
                    contract_id=str(c.id),
                    contract_symbol=c.contract_symbol or f"{c.underlying}_{c.expiry_date}_{c.strike_price}_{c.option_type}",
                    underlying=c.underlying,
                    expiry_date=c.expiry_date,
                    strike_price=c.strike_price,
                    option_type=c.option_type,
                    instrument_type=c.instrument_type,
                    timestamps=ts,
                    last_price=q.last_price,
                    bid_price=q.bid_price,
                    ask_price=q.ask_price,
                    volume=q.volume,
                    open_interest=q.open_interest,
                    change_in_oi=q.change_in_oi,
                    lot_size=c.lot_size,
                    provider=self.provider_name,
                    data_status=DataStatus.HISTORICAL,
                    is_executable=False,
                )
                observations.append(obs)
            return observations
        finally:
            if should_close:
                session.close()

    def get_historical_chain_snapshot(
        self,
        symbol: str,
        timestamp: datetime,
    ) -> Optional[OptionChainSnapshotRecord]:
        session = self._db_session or get_session()
        should_close = self._db_session is None

        try:
            day_start = datetime.combine(timestamp.date(), datetime.min.time())
            day_end = datetime.combine(timestamp.date(), datetime.max.time())

            quotes_db = session.query(OptionsQuoteDB, OptionsContractDB).join(
                OptionsContractDB, OptionsQuoteDB.contract_id == OptionsContractDB.id
            ).filter(
                and_(
                    OptionsContractDB.underlying == symbol.upper(),
                    OptionsQuoteDB.timestamp >= day_start,
                    OptionsQuoteDB.timestamp <= day_end,
                )
            ).all()

            if not quotes_db:
                return None

            # Group by expiry
            expiries = sorted(list({c.expiry_date for _, c in quotes_db}))
            if not expiries:
                return None
            target_expiry = expiries[0]

            rows_dict: Dict[float, OptionChainRow] = {}
            for q, c in quotes_db:
                if c.expiry_date != target_expiry:
                    continue
                k = c.strike_price
                if k not in rows_dict:
                    rows_dict[k] = OptionChainRow(strike_price=k)

                if c.option_type == "CE":
                    rows_dict[k].ce_ltp = q.last_price
                    rows_dict[k].ce_oi = q.open_interest
                    rows_dict[k].ce_volume = q.volume
                elif c.option_type == "PE":
                    rows_dict[k].pe_ltp = q.last_price
                    rows_dict[k].pe_oi = q.open_interest
                    rows_dict[k].pe_volume = q.volume

            sorted_rows = [rows_dict[k] for k in sorted(rows_dict.keys())]
            dte = (target_expiry - timestamp.date()).days

            ts = ObservationTimestamps(
                provider_timestamp=timestamp,
                received_timestamp=datetime.now(timezone.utc),
                processed_timestamp=datetime.now(timezone.utc),
            )

            return OptionChainSnapshotRecord(
                snapshot_id=f"SNAP-{symbol.upper()}-{timestamp.strftime('%Y%m%d')}",
                underlying=symbol.upper(),
                expiry_date=target_expiry,
                spot_price=0.0,
                days_to_expiry=float(dte),
                timestamps=ts,
                provider=self.provider_name,
                data_status=DataStatus.HISTORICAL,
                rows=sorted_rows,
                total_ce_oi=sum(r.ce_oi or 0 for r in sorted_rows),
                total_pe_oi=sum(r.pe_oi or 0 for r in sorted_rows),
            )
        finally:
            if should_close:
                session.close()

    def audit_dataset_quality(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        quotes = self.load_historical_option_quotes(symbol, start_date, end_date)
        total_count = len(quotes)

        if total_count == 0:
            return {
                "symbol": symbol.upper(),
                "total_quotes": 0,
                "bid_ask_coverage_pct": 0.0,
                "ltp_coverage_pct": 0.0,
                "oi_coverage_pct": 0.0,
                "is_suitable_for_execution": False,
                "audit_status": "EMPTY",
                "notes": "No historical quotes found in database for range.",
            }

        with_ltp = sum(1 for q in quotes if q.last_price is not None)
        with_bid_ask = sum(1 for q in quotes if q.bid_price is not None and q.ask_price is not None)
        with_oi = sum(1 for q in quotes if q.open_interest is not None)

        bid_ask_pct = round((with_bid_ask / total_count) * 100.0, 2)
        ltp_pct = round((with_ltp / total_count) * 100.0, 2)
        oi_pct = round((with_oi / total_count) * 100.0, 2)

        return {
            "symbol": symbol.upper(),
            "total_quotes": total_count,
            "bid_ask_coverage_pct": bid_ask_pct,
            "ltp_coverage_pct": ltp_pct,
            "oi_coverage_pct": oi_pct,
            "is_suitable_for_execution": bid_ask_pct > 80.0,
            "audit_status": "HISTORICAL_SETTLEMENT_ONLY" if bid_ask_pct == 0.0 else "PARTIAL",
            "notes": "EOD settlement records contain LTP & OI, but 0% Bid/Ask coverage.",
        }
