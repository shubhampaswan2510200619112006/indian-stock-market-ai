"""
Tests for Point-in-Time Data Guard & Future Contamination Prevention.

CRITICAL GUARANTEE:
At historical simulation time T, ONLY information timestamped <= T may be used.
Future records (> T) MUST be rejected.
"""

from datetime import date, datetime
import pandas as pd
import pytest

from src.ingestion.pipeline import HistoricalDataIngestionPipeline
from src.ingestion.historical_provider import DatabaseHistoricalOptionsProvider


def test_future_data_leakage_rejection():
    """
    Ingests quotes at T=Jan 1 and T=Jan 2.
    Queries snapshot at T=Jan 1 10:00 AM.
    Verifies Jan 2 quote NEVER leaks into Jan 1 snapshot.
    """
    pipeline = HistoricalDataIngestionPipeline()

    data = [
        {
            "underlying": "NIFTY",
            "option_type": "CE",
            "strike_price": 24000.0,
            "expiry_date": "2026-01-28",
            "timestamp": "2026-01-01 10:00:00",
            "last_price": 100.0,
            "bid_price": 99.0,
            "ask_price": 101.0,
            "volume": 500,
            "open_interest": 5000,
        },
        {
            "underlying": "NIFTY",
            "option_type": "CE",
            "strike_price": 24000.0,
            "expiry_date": "2026-01-28",
            "timestamp": "2026-01-02 10:00:00",  # Future quote at T+1
            "last_price": 250.0,  # Huge price surge in future
            "bid_price": 249.0,
            "ask_price": 251.0,
            "volume": 5000,
            "open_interest": 15000,
        },
    ]

    df = pd.DataFrame(data)
    pipeline.ingest_quotes_dataframe(df, source_name="PIT_LEAK_TEST")

    provider = DatabaseHistoricalOptionsProvider()
    
    # Query snapshot at T = Jan 1 10:00:00
    jan1_dt = datetime(2026, 1, 1, 10, 0, 0)
    snap_jan1 = provider.get_historical_chain_snapshot("NIFTY", jan1_dt)

    assert snap_jan1 is not None
    assert snap_jan1.timestamp == jan1_dt
    
    # Retrieve quote from Jan 1 snapshot
    assert len(snap_jan1.strikes) > 0
    ce_quote = snap_jan1.strikes[0].ce
    assert ce_quote is not None
    # Must be Jan 1 price (100.0), NOT future Jan 2 price (250.0)
    assert ce_quote.last_price == 100.0
    assert ce_quote.timestamp == jan1_dt
