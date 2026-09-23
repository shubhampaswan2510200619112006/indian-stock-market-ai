"""
Tests for Historical Options Data Ingestion Pipeline & Quality Audit.
"""

from datetime import date, datetime
import pandas as pd
import pytest

from src.ingestion.pipeline import HistoricalDataIngestionPipeline
from src.ingestion.historical_provider import DatabaseHistoricalOptionsProvider


def test_ingestion_pipeline_parses_and_deduplicates():
    pipeline = HistoricalDataIngestionPipeline()
    
    # Create sample DataFrame
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
        # Duplicate row with same timestamp
        {
            "underlying": "NIFTY",
            "option_type": "CE",
            "strike_price": 24000.0,
            "expiry_date": "2026-01-28",
            "timestamp": "2026-01-01 10:00:00",
            "last_price": 102.0,
            "bid_price": 101.0,
            "ask_price": 103.0,
            "volume": 600,
            "open_interest": 5100,
        },
    ]
    df = pd.DataFrame(data)
    stats = pipeline.ingest_quotes_dataframe(df, source_name="TEST_CSV")

    assert stats.total_parsed == 2
    assert stats.duplicates_skipped == 1
    assert stats.quotes_inserted == 1


def test_dataset_quality_audit():
    provider = DatabaseHistoricalOptionsProvider()
    report = provider.audit_dataset_quality(
        symbol="NIFTY",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 2, 1),
    )
    assert report.symbol == "NIFTY"
    assert report.data_source == "DATABASE_HISTORICAL_PROVIDER"
