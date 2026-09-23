"""
Tests for Real Historical Data Ingestion (NSE Bhavcopy Importer).
"""

from datetime import date
import pytest
from src.ingestion.nse_bhavcopy_importer import NSEBhavcopyOptionsProvider
from src.database.connection import get_session
from src.database.models import OptionsQuoteDB, EquityPriceDB


def test_ingest_genuine_nifty_options_dataset():
    provider = NSEBhavcopyOptionsProvider()
    stats = provider.ingest_genuine_nifty_options_dataset(symbol="NIFTY", days_back=10)

    assert stats.quotes_inserted > 0
    assert not stats.errors

    session = get_session()
    q_count = session.query(OptionsQuoteDB).count()
    eq_count = session.query(EquityPriceDB).count()
    session.close()

    assert q_count >= stats.quotes_inserted
    assert eq_count > 0
