"""
Tests for Database State Audit Module.
"""

import pytest
from src.ingestion.audit_state import audit_current_database_state


def test_audit_current_database_state():
    report = audit_current_database_state()
    assert report is not None
    assert isinstance(report.underlyings_count, int)
    assert isinstance(report.options_quotes_count, int)
