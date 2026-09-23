"""
Tests for Phase 9 Ingestion Checkpointing & Auditable Failover.
"""

from datetime import datetime, timezone
import pytest

from src.data_infrastructure.health_monitor import ProviderHealthMonitor
from src.data_infrastructure.ingestion_pipeline import ResumableIngestionPipeline
from src.data_infrastructure.models import (
    DataStatus,
    MarketObservation,
    ObservationTimestamps,
)


import uuid

def test_ingestion_pipeline_batch_lifecycle_and_idempotency():
    pipeline = ResumableIngestionPipeline(provider_name="TEST_PROVIDER")
    unique_sym = f"NIFTY_{uuid.uuid4().hex[:6]}"
    batch_id = pipeline.start_batch(requested_instruments=[unique_sym])
    assert batch_id.startswith("BATCH-")

    now = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
    obs = MarketObservation(
        observation_id=f"TEST-IDEM-{uuid.uuid4().hex[:6]}",
        provider="TEST_PROVIDER",
        provider_symbol="^NSEI",
        symbol=unique_sym,
        timestamps=ObservationTimestamps(provider_timestamp=now, received_timestamp=now),
        last_price=22000.0,
        data_status=DataStatus.HISTORICAL,
        raw_payload={"test": 123},
    )

    # First ingest
    res1 = pipeline.process_and_persist_observations([obs], batch_id=batch_id)
    assert res1["accepted"] == 1

    # Second ingest with same observation -> idempotent skip (zero duplicated records)
    res2 = pipeline.process_and_persist_observations([obs], batch_id=batch_id)
    assert res2["accepted"] == 0

    pipeline.finalize_batch(batch_id=batch_id, status="COMPLETED")


def test_provider_failover_records_auditable_transition():
    # Failover must never silently splice providers
    event = ProviderHealthMonitor.record_failover_transition(
        previous_provider="PRIMARY_FEED",
        new_provider="BACKUP_FEED",
        reason="PRIMARY_FEED socket disconnected for > 30s",
        affected_instruments=["NIFTY", "BANKNIFTY"],
        notes="Failover test transition.",
    )
    assert event.event_id.startswith("TRN-")
    assert event.previous_provider == "PRIMARY_FEED"
    assert event.new_provider == "BACKUP_FEED"

    history = ProviderHealthMonitor.get_transition_history()
    assert len(history) >= 1
    assert history[-1]["previous_provider"] == "PRIMARY_FEED"
