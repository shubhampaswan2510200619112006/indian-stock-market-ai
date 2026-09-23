"""
Tests for Genuine End-to-End Historical Options Backtest on Database Quotes.
"""

from datetime import date, datetime
import pytest

from src.backtesting.models import BacktestConfig
from src.backtesting.engine import BacktestEngine
from src.backtesting.data_gate import DataGate, DataAvailabilityStatus
from src.ingestion.nse_bhavcopy_importer import NSEBhavcopyOptionsProvider
from src.database.connection import get_session
from src.database.models import OptionsQuoteDB, EquityPriceDB


def test_genuine_historical_options_backtest_execution():
    """
    Ingests genuine historical NIFTY options and equity prices into DB.
    Executes BacktestEngine configured WITH use_synthetic_if_unavailable=False.
    Verifies that the backtester runs cleanly on real DB quotes.
    """
    provider = NSEBhavcopyOptionsProvider()
    provider.ingest_genuine_nifty_options_dataset(symbol="NIFTY", days_back=20)

    session = get_session()
    q_min_dt = session.query(OptionsQuoteDB.timestamp).order_by(OptionsQuoteDB.timestamp.asc()).first()
    q_max_dt = session.query(OptionsQuoteDB.timestamp).order_by(OptionsQuoteDB.timestamp.desc()).first()
    session.close()

    assert q_min_dt is not None and q_max_dt is not None

    start_d = q_min_dt[0].date()
    end_d = q_max_dt[0].date()

    gate = DataGate()
    report = gate.evaluate_availability("NIFTY", start_d, end_d, min_option_quotes=50)
    assert report.status in [DataAvailabilityStatus.AVAILABLE, DataAvailabilityStatus.PARTIAL]

    config = BacktestConfig(
        symbol="NIFTY",
        start_date=start_d,
        end_date=end_d,
        initial_equity=1_000_000.0,
        strategy_name="Bull Call Spread",
        min_strategy_score=40.0,
        use_synthetic_if_unavailable=False,  # Enforces DB quote usage!
    )

    engine = BacktestEngine(config)
    result = engine.run()

    assert result.data_source != "NONE"
    assert "DATABASE" in result.data_source or "SYNTHETIC" not in result.data_source
    assert result.metrics is not None
