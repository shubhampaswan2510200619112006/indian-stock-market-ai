"""
Phase 9 — Resumable Ingestion Pipeline & Raw Data Preservation.

Implements:
- Resumable ingestion batches with database-backed checkpoints.
- Idempotent observation deduplication.
- Exponential backoff retry logic.
- Separation of RAW -> NORMALIZED -> VALIDATED stages.
- Complete preservation of raw provider response payloads.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import time
from typing import Any, Callable, Dict, List, Optional
import uuid

from src.database.connection import get_session
from src.database.models import IngestionBatchDB, MarketObservationDB
from src.data_infrastructure.models import MarketObservation
from src.data_infrastructure.quality_engine import DataQualityEngine


class ResumableIngestionPipeline:
    """
    Orchestrates robust, checkpointed ingestion jobs.
    """

    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    def start_batch(self, requested_instruments: List[str]) -> str:
        """Initializes a new ingestion batch record in database."""
        batch_id = f"BATCH-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        session = get_session()
        try:
            db_batch = IngestionBatchDB(
                batch_id=batch_id,
                provider=self.provider_name,
                start_time=now,
                requested_instruments=requested_instruments,
                records_received=0,
                records_accepted=0,
                records_quarantined=0,
                status="RUNNING",
                checkpoint_data={"last_processed_index": 0, "completed_symbols": []},
            )
            session.add(db_batch)
            session.commit()
            return batch_id
        finally:
            session.close()

    def update_checkpoint(
        self,
        batch_id: str,
        checkpoint_data: Dict[str, Any],
        received_increment: int = 0,
        accepted_increment: int = 0,
        quarantined_increment: int = 0,
    ) -> None:
        """Updates batch checkpoint and running counts."""
        session = get_session()
        try:
            batch = session.query(IngestionBatchDB).filter(IngestionBatchDB.batch_id == batch_id).first()
            if batch:
                batch.checkpoint_data = checkpoint_data
                batch.records_received += received_increment
                batch.records_accepted += accepted_increment
                batch.records_quarantined += quarantined_increment
                session.commit()
        finally:
            session.close()

    def finalize_batch(self, batch_id: str, status: str = "COMPLETED", error_log: Optional[str] = None) -> None:
        """Marks an ingestion batch as finished."""
        session = get_session()
        try:
            batch = session.query(IngestionBatchDB).filter(IngestionBatchDB.batch_id == batch_id).first()
            if batch:
                batch.status = status
                batch.end_time = datetime.now(timezone.utc)
                if error_log:
                    batch.error_log = error_log
                session.commit()
        finally:
            session.close()

    def process_and_persist_observations(
        self,
        observations: List[MarketObservation],
        batch_id: str,
    ) -> Dict[str, int]:
        """
        Validates, deduplicates, and commits observations to database.
        Quarantines invalid records without losing raw payloads.
        """
        session = get_session()
        accepted = 0
        quarantined = 0

        try:
            for obs in observations:
                obs.ingestion_batch_id = batch_id

                # Deduplication check: same provider, symbol, and provider_timestamp
                p_ts = obs.timestamps.provider_timestamp
                existing = session.query(MarketObservationDB).filter(
                    MarketObservationDB.provider == obs.provider,
                    MarketObservationDB.symbol == obs.symbol,
                    MarketObservationDB.provider_timestamp == p_ts,
                ).first()

                if existing:
                    # Idempotent skip: do not duplicate identical observation
                    continue

                # Run quality engine validation
                qc_result = DataQualityEngine.validate_and_quarantine_market_obs(obs)

                if not qc_result.is_valid:
                    quarantined += 1
                    obs.validation_status = f"QUARANTINED:{qc_result.rule_violated}"
                else:
                    accepted += 1
                    obs.validation_status = "VALID"

                # Persist to database (preserving raw payload regardless of quarantine)
                db_obs = MarketObservationDB(
                    observation_id=obs.observation_id,
                    provider=obs.provider,
                    provider_symbol=obs.provider_symbol,
                    symbol=obs.symbol,
                    provider_timestamp=obs.timestamps.provider_timestamp,
                    received_timestamp=obs.timestamps.received_timestamp,
                    processed_timestamp=obs.timestamps.processed_timestamp,
                    last_price=obs.last_price,
                    bid_price=obs.bid_price,
                    ask_price=obs.ask_price,
                    volume=obs.volume,
                    open_interest=obs.open_interest,
                    data_status=obs.data_status.value,
                    validation_status=obs.validation_status,
                    is_executable=1 if obs.is_executable else 0,
                    raw_payload=obs.raw_payload,
                    batch_id=batch_id,
                    dataset_id=obs.dataset_id,
                    dataset_version=obs.dataset_version,
                )
                session.add(db_obs)

            session.commit()

            # Update batch statistics
            self.update_checkpoint(
                batch_id=batch_id,
                checkpoint_data={"last_update": datetime.now(timezone.utc).isoformat()},
                received_increment=len(observations),
                accepted_increment=accepted,
                quarantined_increment=quarantined,
            )

            return {"received": len(observations), "accepted": accepted, "quarantined": quarantined}
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    def execute_with_retry(
        func: Callable[[], Any],
        max_retries: int = 3,
        initial_backoff_sec: float = 0.5,
    ) -> Any:
        """Executes a provider call with exponential backoff retry logic."""
        backoff = initial_backoff_sec
        last_exception = None

        for attempt in range(1, max_retries + 1):
            try:
                return func()
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    time.sleep(backoff)
                    backoff *= 2.0
                else:
                    raise last_exception
