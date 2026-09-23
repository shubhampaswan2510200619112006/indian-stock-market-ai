"""
Tests for Phase 9 Timestamp Architecture & Clock-Skew Detection.
"""

from datetime import datetime, timedelta, timezone
import pytest

from src.data_infrastructure.models import ObservationTimestamps


def test_valid_timestamp_ordering():
    now = datetime.now(timezone.utc)
    ts = ObservationTimestamps(
        provider_timestamp=now - timedelta(seconds=10),
        received_timestamp=now,
        processed_timestamp=now + timedelta(milliseconds=5),
        request_timestamp=now - timedelta(milliseconds=100),
        response_timestamp=now,
    )
    is_valid, msg = ts.validate_ordering()
    assert is_valid is True
    assert msg == "VALID_TIMESTAMPS"

    latencies = ts.calculate_latencies()
    assert latencies["network_request_to_response_ms"] is not None
    assert latencies["provider_to_received_latency_ms"] is not None
    assert latencies["received_to_processed_latency_ms"] is not None


def test_processed_preceding_received_rejected():
    now = datetime.now(timezone.utc)
    ts = ObservationTimestamps(
        provider_timestamp=now,
        received_timestamp=now,
        processed_timestamp=now - timedelta(seconds=1),  # Impossible
    )
    is_valid, msg = ts.validate_ordering()
    assert is_valid is False
    assert "precedes received_timestamp" in msg


def test_future_provider_timestamp_clock_skew_rejected():
    now = datetime.now(timezone.utc)
    ts = ObservationTimestamps(
        provider_timestamp=now + timedelta(seconds=300),  # 5 minutes in future!
        received_timestamp=now,
        processed_timestamp=now + timedelta(milliseconds=1),
    )
    is_valid, msg = ts.validate_ordering()
    assert is_valid is False
    assert "in future relative to received_timestamp" in msg


def test_delayed_historical_timestamps_accepted():
    # Historical observations from 30 days ago received today must be valid
    old_time = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    ts = ObservationTimestamps(
        provider_timestamp=old_time,
        received_timestamp=now,
        processed_timestamp=now + timedelta(milliseconds=2),
    )
    is_valid, msg = ts.validate_ordering()
    assert is_valid is True
