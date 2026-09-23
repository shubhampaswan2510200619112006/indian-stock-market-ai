"""
Phase 14 Dataset Versioning and Cryptographic Content-Identity Engine.

Tracks immutable version lineages for market datasets based on cryptographic SHA256 hashes.
Ensures that any file replacement or content alteration generates a distinct new version
rather than overwriting an existing certified dataset version.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class DatasetVersionRecord:
    dataset_id: str
    version_id: str  # e.g., "v1", "v2"
    sha256: str
    source: str
    vendor: str
    received_at: str
    schema_version: str = "phase14_v1"
    validation_version: str = "cert_v1"
    calendar_version: str = "nse_cal_v1"
    normalization_version: str = "raw_v1"
    license_record: Optional[str] = None
    parent_version: Optional[str] = None
    is_certified: bool = False
    certification_timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DatasetVersionRegistry:
    """
    Manages cryptographic version tracking and ensures immutability of certified datasets.
    """

    def __init__(self):
        self.versions: Dict[str, List[DatasetVersionRecord]] = {}

    def register_version(
        self,
        dataset_id: str,
        sha256: str,
        source: str,
        vendor: str,
        license_record: Optional[str] = None,
        schema_version: str = "phase14_v1",
        validation_version: str = "cert_v1",
        calendar_version: str = "nse_cal_v1",
        normalization_version: str = "raw_v1",
    ) -> DatasetVersionRecord:
        """
        Registers a new dataset version or returns the existing matching version by SHA256.
        """
        history = self.versions.get(dataset_id, [])

        # If identical content hash already exists, return existing version
        for rec in history:
            if rec.sha256 == sha256:
                return rec

        parent_version = history[-1].version_id if history else None
        version_num = len(history) + 1
        version_id = f"v{version_num}"

        record = DatasetVersionRecord(
            dataset_id=dataset_id,
            version_id=version_id,
            sha256=sha256,
            source=source,
            vendor=vendor,
            received_at=datetime.now(timezone.utc).isoformat(),
            schema_version=schema_version,
            validation_version=validation_version,
            calendar_version=calendar_version,
            normalization_version=normalization_version,
            license_record=license_record,
            parent_version=parent_version,
            is_certified=False,
        )
        if dataset_id not in self.versions:
            self.versions[dataset_id] = []
        self.versions[dataset_id].append(record)
        return record

    def mark_certified(self, dataset_id: str, version_id: str) -> bool:
        """Marks a specific dataset version as certified."""
        history = self.versions.get(dataset_id, [])
        for rec in history:
            if rec.version_id == version_id:
                rec.is_certified = True
                rec.certification_timestamp = datetime.now(timezone.utc).isoformat()
                return True
        return False

    def get_latest_version(self, dataset_id: str) -> Optional[DatasetVersionRecord]:
        history = self.versions.get(dataset_id, [])
        return history[-1] if history else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_datasets": len(self.versions),
            "versions": {k: [v.to_dict() for v in val] for k, val in self.versions.items()},
        }
