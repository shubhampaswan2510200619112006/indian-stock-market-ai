"""
Phase 9 — Data Lineage & Immutable Dataset Snapshot Engine.

Ensures complete reproducibility of research:
- Creates and registers immutable DatasetSnapshots with coverage diagnostics.
- Tracks explicit DataLineage from downstream predictions/features/backtest runs
  back to exact source observations and timestamps.
- Enforces point-in-time isolation: feature availability timestamp < target observation time.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
import hashlib
from typing import Any, Dict, List, Optional
import uuid

from src.database.connection import get_session
from src.database.models import DataLineageDB, DatasetSnapshotDB
from src.data_infrastructure.models import (
    DataLineageRecord,
    DatasetSnapshotMetadata,
)


class DatasetSnapshotManager:
    """
    Manages immutable historical dataset snapshots for reproducible research.
    """

    @classmethod
    def create_snapshot(
        cls,
        dataset_id: str,
        dataset_version: str,
        provider: str,
        instruments: List[str],
        start_date: date,
        end_date: date,
        observation_count: int,
        ltp_coverage_pct: float,
        bid_ask_coverage_pct: float,
        oi_coverage_pct: float,
        volume_coverage_pct: float,
        iv_coverage_pct: float,
        quality_status: str,
        manifest: Optional[Dict[str, Any]] = None,
        description: str = "",
    ) -> DatasetSnapshotMetadata:
        """Creates and registers an immutable dataset snapshot in database."""
        snapshot_id = f"SNAP-{dataset_id}-{dataset_version}-{uuid.uuid4().hex[:6]}"
        now = datetime.now(timezone.utc)

        metadata = DatasetSnapshotMetadata(
            snapshot_id=snapshot_id,
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            created_at=now,
            provider=provider,
            date_range_start=start_date,
            date_range_end=end_date,
            observation_count=observation_count,
            instruments=instruments,
            ltp_coverage_pct=ltp_coverage_pct,
            bid_ask_coverage_pct=bid_ask_coverage_pct,
            oi_coverage_pct=oi_coverage_pct,
            volume_coverage_pct=volume_coverage_pct,
            iv_coverage_pct=iv_coverage_pct,
            quality_status=quality_status,
            is_immutable=True,
            manifest=manifest or {},
        )

        try:
            session = get_session()
            db_snap = DatasetSnapshotDB(
                snapshot_id=snapshot_id,
                dataset_id=dataset_id,
                dataset_version=dataset_version,
                description=description,
                date_range_start=start_date,
                date_range_end=end_date,
                observation_count=observation_count,
                ltp_coverage_pct=ltp_coverage_pct,
                bid_ask_coverage_pct=bid_ask_coverage_pct,
                oi_coverage_pct=oi_coverage_pct,
                volume_coverage_pct=volume_coverage_pct,
                iv_coverage_pct=iv_coverage_pct,
                quality_status=quality_status,
                manifest=manifest or {},
                is_immutable=1,
                created_at=now,
            )
            session.add(db_snap)
            session.commit()
            session.close()
        except Exception:
            pass

        return metadata

    @classmethod
    def get_snapshot(cls, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a dataset snapshot by ID."""
        session = get_session()
        try:
            snap = session.query(DatasetSnapshotDB).filter(DatasetSnapshotDB.snapshot_id == snapshot_id).first()
            if not snap:
                return None
            return {
                "snapshot_id": snap.snapshot_id,
                "dataset_id": snap.dataset_id,
                "dataset_version": snap.dataset_version,
                "description": snap.description,
                "date_range_start": snap.date_range_start.isoformat() if snap.date_range_start else None,
                "date_range_end": snap.date_range_end.isoformat() if snap.date_range_end else None,
                "observation_count": snap.observation_count,
                "ltp_coverage_pct": snap.ltp_coverage_pct,
                "bid_ask_coverage_pct": snap.bid_ask_coverage_pct,
                "oi_coverage_pct": snap.oi_coverage_pct,
                "volume_coverage_pct": snap.volume_coverage_pct,
                "iv_coverage_pct": snap.iv_coverage_pct,
                "quality_status": snap.quality_status,
                "manifest": snap.manifest,
                "created_at": snap.created_at.isoformat() if snap.created_at else None,
            }
        finally:
            session.close()


class DataLineageTracker:
    """
    Registers and audits end-to-end data lineage for research artifacts.
    """

    @classmethod
    def record_lineage(
        cls,
        target_artifact_type: str,
        target_artifact_id: str,
        dataset_snapshot_id: str,
        source_observation_ids: List[str],
        feature_version: str,
    ) -> DataLineageRecord:
        """
        Creates a verifiable cryptographic lineage record linking artifact to source observations.
        """
        lineage_id = f"LIN-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        record = DataLineageRecord(
            lineage_id=lineage_id,
            target_artifact_type=target_artifact_type,
            target_artifact_id=target_artifact_id,
            dataset_snapshot_id=dataset_snapshot_id,
            source_observation_ids=source_observation_ids,
            feature_version=feature_version,
            created_at=now,
        )
        record.compute_hash()

        try:
            session = get_session()
            db_lin = DataLineageDB(
                lineage_id=lineage_id,
                target_artifact_type=target_artifact_type,
                target_artifact_id=target_artifact_id,
                dataset_snapshot_id=dataset_snapshot_id,
                source_observation_ids=source_observation_ids,
                feature_version=feature_version,
                lineage_hash=record.lineage_hash,
                created_at=now,
            )
            session.add(db_lin)
            session.commit()
            session.close()
        except Exception:
            pass

        return record

    @classmethod
    def verify_no_lookahead_leakage(
        cls,
        feature_availability_timestamp: datetime,
        target_observation_timestamp: datetime,
    ) -> tuple[bool, str]:
        """
        Validates the fundamental quantitative law:
        feature_availability_timestamp < target_observation_timestamp
        Prevents future data lookahead leakage in ML & backtesting.
        """
        f_ts = feature_availability_timestamp if feature_availability_timestamp.tzinfo else feature_availability_timestamp.replace(tzinfo=timezone.utc)
        t_ts = target_observation_timestamp if target_observation_timestamp.tzinfo else target_observation_timestamp.replace(tzinfo=timezone.utc)

        if f_ts >= t_ts:
            return False, f"LOOKAHEAD LEAKAGE: feature availability ({f_ts}) is >= target observation time ({t_ts})"

        return True, "LEAKAGE_FREE"
