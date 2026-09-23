"""
Tests for Phase 9 Data Lineage, Dataset Snapshots & Lookahead Leakage Prevention.
"""

from datetime import date, datetime, timedelta, timezone
import pytest

from src.data_infrastructure.lineage import DataLineageTracker, DatasetSnapshotManager


def test_immutable_dataset_snapshot_creation():
    meta = DatasetSnapshotManager.create_snapshot(
        dataset_id="TEST_DATASET",
        dataset_version="v1.0",
        provider="YFINANCE",
        instruments=["NIFTY", "BANKNIFTY"],
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        observation_count=500,
        ltp_coverage_pct=100.0,
        bid_ask_coverage_pct=0.0,
        oi_coverage_pct=0.0,
        volume_coverage_pct=100.0,
        iv_coverage_pct=0.0,
        quality_status="PARTIALLY_VALIDATED",
        description="Automated unit test snapshot.",
    )
    assert meta.snapshot_id.startswith("SNAP-TEST_DATASET-v1.0")
    assert meta.is_immutable is True
    assert meta.observation_count == 500


def test_data_lineage_cryptographic_hash():
    lin = DataLineageTracker.record_lineage(
        target_artifact_type="FEATURE_ROW",
        target_artifact_id="FEAT-20250101-NIFTY",
        dataset_snapshot_id="SNAP-1",
        source_observation_ids=["OBS-1", "OBS-2", "OBS-3"],
        feature_version="v2.1",
    )
    assert lin.lineage_id.startswith("LIN-")
    assert len(lin.lineage_hash) == 64  # SHA-256


def test_lookahead_leakage_detection():
    now = datetime.now(timezone.utc)

    # Valid: Feature available before target observation
    valid, _ = DataLineageTracker.verify_no_lookahead_leakage(
        feature_availability_timestamp=now - timedelta(minutes=5),
        target_observation_timestamp=now,
    )
    assert valid is True

    # Leakage: Feature availability is >= target observation!
    leakage, msg = DataLineageTracker.verify_no_lookahead_leakage(
        feature_availability_timestamp=now + timedelta(seconds=1),
        target_observation_timestamp=now,
    )
    assert leakage is False
    assert "LOOKAHEAD LEAKAGE" in msg
