"""
Tests for Data Availability Gate.
"""

from datetime import date
import pytest
from src.backtesting.data_gate import DataGate, DataAvailabilityStatus


def test_data_gate_empty_db_returns_unavailable():
    gate = DataGate()
    report = gate.evaluate_availability(
        symbol="NIFTY",
        start_date=date(2030, 1, 1),
        end_date=date(2030, 2, 1),
    )
    
    assert report.status == DataAvailabilityStatus.UNAVAILABLE
    assert "HISTORICAL OPTIONS DATA INSUFFICIENT FOR VALID BACKTEST" in report.message
    assert len(report.missing_elements) > 0
