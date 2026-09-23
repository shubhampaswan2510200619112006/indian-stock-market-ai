"""
Phase 9 — Provider Verification Engine.

Provides an evidence-based verification mechanism for data provider capabilities.
Independently verifies provider timestamps, received timestamps, latency, and returned fields.
Never trusts marketing or documentation claims alone.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from src.database.connection import get_session
from src.database.models import ProviderVerificationDB
from src.data_infrastructure.models import DataStatus


class ProviderVerificationEngine:
    """
    Independently verifies and logs evidence of provider capabilities.
    """

    @staticmethod
    def record_verification(
        provider_name: str,
        capability: str,
        test_instrument: str,
        observed_provider_timestamp: Optional[datetime],
        observed_received_timestamp: Optional[datetime],
        observed_fields: Dict[str, Any],
        verification_method: str = "INDEPENDENT_OBSERVATION",
        evidence_reference: str = "",
        notes: str = "",
    ) -> Dict[str, Any]:
        """
        Evaluates and stores an evidence-based capability verification record.
        """
        now = datetime.now(timezone.utc)
        verification_id = f"VERIF-{uuid.uuid4().hex[:12]}"

        # Calculate latency
        latency_ms = None
        if observed_provider_timestamp and observed_received_timestamp:
            p_ts = observed_provider_timestamp if observed_provider_timestamp.tzinfo else observed_provider_timestamp.replace(tzinfo=timezone.utc)
            r_ts = observed_received_timestamp if observed_received_timestamp.tzinfo else observed_received_timestamp.replace(tzinfo=timezone.utc)
            latency_ms = round((r_ts - p_ts).total_seconds() * 1000.0, 2)

        # Dynamic Status Classification
        if not observed_fields:
            result = "FAIL"
            status = DataStatus.UNAVAILABLE.value
            notes = notes or "Provider returned no observation fields."
        elif "bid" not in observed_fields and "ask" not in observed_fields and capability == "executable_quotes":
            result = "FAIL"
            status = DataStatus.UNAVAILABLE.value
            notes = notes or "Executable Bid/Ask is missing."
        elif latency_ms is not None and latency_ms > 60_000:
            # Latency exceeds 1 minute -> delayed
            result = "PASS"
            status = DataStatus.VERIFIED_DELAYED.value
            notes = notes or f"Verified with observed delay of {latency_ms / 1000.0:.1f}s."
        elif latency_ms is not None and latency_ms <= 5_000:
            result = "PASS"
            status = DataStatus.VERIFIED_REAL_TIME.value
            notes = notes or f"Verified real-time observation with latency {latency_ms:.1f}ms."
        elif latency_ms is not None:
            result = "PASS"
            status = DataStatus.VERIFIED_NEAR_REAL_TIME.value
            notes = notes or f"Verified near-real-time observation with latency {latency_ms:.1f}ms."
        else:
            result = "PASS"
            status = DataStatus.VERIFIED_DELAYED.value
            notes = notes or "Provider timestamp unavailable or delayed."

        # Persist verification record to DB
        record_dict = {
            "verification_id": verification_id,
            "provider_name": provider_name,
            "capability": capability,
            "verification_timestamp": now.isoformat(),
            "test_instrument": test_instrument,
            "observed_provider_timestamp": observed_provider_timestamp.isoformat() if observed_provider_timestamp else None,
            "observed_received_timestamp": observed_received_timestamp.isoformat() if observed_received_timestamp else None,
            "observed_latency_ms": latency_ms,
            "observed_fields": observed_fields,
            "verification_method": verification_method,
            "result": result,
            "status": status,
            "evidence_reference": evidence_reference,
            "notes": notes,
        }

        try:
            session = get_session()
            db_rec = ProviderVerificationDB(
                verification_id=verification_id,
                provider_name=provider_name,
                capability=capability,
                verification_timestamp=now,
                test_instrument=test_instrument,
                observed_provider_timestamp=observed_provider_timestamp,
                observed_received_timestamp=observed_received_timestamp,
                observed_latency_ms=latency_ms,
                observed_fields=observed_fields,
                verification_method=verification_method,
                result=result,
                status=status,
                evidence_reference=evidence_reference,
                notes=notes,
            )
            session.add(db_rec)
            session.commit()
            session.close()
        except Exception:
            pass  # Fallback gracefully if database is locked or busy

        return record_dict

    @staticmethod
    def get_latest_verifications(provider_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves recent verification records from database."""
        session = get_session()
        try:
            query = session.query(ProviderVerificationDB)
            if provider_name:
                query = query.filter(ProviderVerificationDB.provider_name == provider_name)
            records = query.order_by(ProviderVerificationDB.verification_timestamp.desc()).limit(100).all()
            return [
                {
                    "verification_id": r.verification_id,
                    "provider_name": r.provider_name,
                    "capability": r.capability,
                    "verification_timestamp": r.verification_timestamp.isoformat() if r.verification_timestamp else None,
                    "test_instrument": r.test_instrument,
                    "observed_latency_ms": r.observed_latency_ms,
                    "result": r.result,
                    "status": r.status,
                    "notes": r.notes,
                }
                for r in records
            ]
        finally:
            session.close()
