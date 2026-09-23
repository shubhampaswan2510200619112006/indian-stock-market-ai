"""
Historical Options Ingestion Pipeline.

PIPELINE STEPS:
RAW DATA -> PARSE -> NORMALIZE -> VALIDATE -> DEDUPLICATE -> TIMESTAMP NORMALIZATION -> CONTRACT VALIDATION -> DATABASE

CRITICAL RULE:
Missing values (bid/ask/OI/volume) remain NULL. Never invent numbers!
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database.connection import get_session
from src.database.models import OptionsContractDB, OptionsQuoteDB, EquityPriceDB
from src.ingestion.schemas import DataQualityStatus, OptionQuote, OptionType


class IngestionStats(BaseModel):
    total_parsed: int = 0
    contracts_created: int = 0
    quotes_inserted: int = 0
    duplicates_skipped: int = 0
    invalid_skipped: int = 0
    errors: List[str] = []


class HistoricalDataIngestionPipeline:
    """
    Parses, validates, normalizes, deduplicates, and ingests historical option chain records into SQLite/PostgreSQL.
    """

    def __init__(self, db_session: Optional[Session] = None):
        self._db_session = db_session

    def ingest_quotes_dataframe(
        self,
        df: pd.DataFrame,
        source_name: str = "CSV_IMPORT",
    ) -> IngestionStats:
        """
        Ingests a DataFrame containing historical option quotes.
        Expected columns:
        - underlying (str)
        - option_type (str: 'CE' or 'PE')
        - strike_price (float)
        - expiry_date (date or str 'YYYY-MM-DD')
        - timestamp (datetime or str 'YYYY-MM-DD HH:MM:SS')
        - last_price (float)
        - bid_price (optional float)
        - ask_price (optional float)
        - volume (optional int)
        - open_interest (optional int)
        - lot_size (optional int, default=25)
        """
        stats = IngestionStats()
        if df.empty:
            stats.errors.append("Empty DataFrame provided.")
            return stats

        session = self._db_session if self._db_session else get_session()
        should_close = self._db_session is None

        try:
            # Step 1: Parse & Normalize
            df_norm = df.copy()
            stats.total_parsed = len(df_norm)

            required_cols = ["underlying", "option_type", "strike_price", "expiry_date", "timestamp", "last_price"]
            for col in required_cols:
                if col not in df_norm.columns:
                    stats.errors.append(f"Missing required column: {col}")
                    return stats

            # Clean dates
            df_norm["expiry_date"] = pd.to_datetime(df_norm["expiry_date"]).dt.date
            df_norm["timestamp"] = pd.to_datetime(df_norm["timestamp"])

            # Step 2: Validate prices & moneyness
            valid_mask = (
                (df_norm["strike_price"] > 0)
                & (df_norm["last_price"] >= 0)
                & (df_norm["option_type"].isin(["CE", "PE"]))
            )
            invalid_count = len(df_norm) - valid_mask.sum()
            stats.invalid_skipped = invalid_count
            df_valid = df_norm[valid_mask].copy()

            # Step 3: Deduplicate on (underlying, option_type, strike_price, expiry_date, timestamp)
            dedup_cols = ["underlying", "option_type", "strike_price", "expiry_date", "timestamp"]
            before_dedup = len(df_valid)
            df_clean = df_valid.drop_duplicates(subset=dedup_cols, keep="last")
            stats.duplicates_skipped = before_dedup - len(df_clean)

            # Step 4: Contract Registration & Contract ID Cache
            contract_cache: Dict[Tuple[str, str, float, date], int] = {}

            # Fetch existing contracts
            existing_contracts = session.query(OptionsContractDB).all()
            for c in existing_contracts:
                contract_cache[(c.underlying, c.option_type, c.strike_price, c.expiry_date)] = c.id

            # Create missing contracts
            for _, row in df_clean.drop_duplicates(subset=["underlying", "option_type", "strike_price", "expiry_date"]).iterrows():
                key = (row["underlying"], row["option_type"], float(row["strike_price"]), row["expiry_date"])
                if key not in contract_cache:
                    lot_sz = int(row.get("lot_size", 25)) if pd.notnull(row.get("lot_size")) else 25
                    inst_type = str(row.get("instrument_type")) if pd.notnull(row.get("instrument_type")) else "INDEX_OPTION"
                    c_obj = OptionsContractDB(
                        underlying=row["underlying"],
                        exchange="NSE",
                        instrument_type=inst_type,
                        option_type=row["option_type"],
                        strike_price=float(row["strike_price"]),
                        expiry_date=row["expiry_date"],
                        contract_symbol=f"{row['underlying']}{row['expiry_date'].strftime('%y%b').upper()}{int(row['strike_price'])}{row['option_type']}",
                        lot_size=lot_sz,
                    )
                    session.add(c_obj)
                    session.flush()
                    contract_cache[key] = c_obj.id
                    stats.contracts_created += 1

            # Step 5: Insert timestamped quotes
            quote_objs: List[OptionsQuoteDB] = []
            for _, row in df_clean.iterrows():
                key = (row["underlying"], row["option_type"], float(row["strike_price"]), row["expiry_date"])
                contract_id = contract_cache[key]

                bid = float(row["bid_price"]) if pd.notnull(row.get("bid_price")) else None
                ask = float(row["ask_price"]) if pd.notnull(row.get("ask_price")) else None
                vol = int(row["volume"]) if pd.notnull(row.get("volume")) else None
                oi = int(row["open_interest"]) if pd.notnull(row.get("open_interest")) else None

                q_obj = OptionsQuoteDB(
                    contract_id=contract_id,
                    timestamp=row["timestamp"].to_pydatetime(),
                    last_price=float(row["last_price"]),
                    bid_price=bid,
                    ask_price=ask,
                    volume=vol,
                    open_interest=oi,
                    source=source_name,
                    data_quality="GOOD" if (bid is not None and ask is not None) else "PARTIAL",
                )
                quote_objs.append(q_obj)

            session.bulk_save_objects(quote_objs)
            session.commit()
            stats.quotes_inserted = len(quote_objs)

        except Exception as e:
            session.rollback()
            stats.errors.append(f"Ingestion exception: {str(e)}")
        finally:
            if should_close:
                session.close()

        return stats
