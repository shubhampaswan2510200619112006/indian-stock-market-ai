"""
Phase 13 Dataset Manifest, Provenance, and Content-Based Versioning.

Enforces:
1. Content-based immutable versioning based on SHA256 checksums.
2. Identical checksum detection (avoids redundant versions).
3. Strict category isolation: PRODUCTION_DATA, TEST_FIXTURES, SYNTHETIC_TEST_DATA, AUXILIARY_DATASET.
4. Independent dataset license states: LICENSE_VERIFIED, LICENSE_PENDING, LICENSE_RESTRICTED, LICENSE_UNKNOWN, LICENSE_REJECTED.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class DatasetCategory(str, Enum):
    PRODUCTION_DATA = "PRODUCTION_DATA"
    TEST_FIXTURES = "TEST_FIXTURES"
    SYNTHETIC_TEST_DATA = "SYNTHETIC_TEST_DATA"
    AUXILIARY_DATASET = "AUXILIARY_DATASET"


class LicenseStatus(str, Enum):
    LICENSE_VERIFIED = "LICENSE_VERIFIED"
    LICENSE_PENDING = "LICENSE_PENDING"
    LICENSE_RESTRICTED = "LICENSE_RESTRICTED"
    LICENSE_UNKNOWN = "LICENSE_UNKNOWN"
    LICENSE_REJECTED = "LICENSE_REJECTED"


@dataclass
class DatasetManifest:
    dataset_id: str
    version: str  # e.g., "v1", "v2"
    category: DatasetCategory
    vendor: str
    product_name: str
    underlying: str  # e.g., "NIFTY", "BANKNIFTY"
    frequency: str  # e.g., "1m", "5m", "tick", "eod"
    coverage_start: str
    coverage_end: str
    total_records: int
    source_file: str
    source_checksum: str  # SHA256
    schema_version: str
    transformation_version: str
    validation_version: str
    acquisition_timestamp: str
    license_status: LicenseStatus = LicenseStatus.LICENSE_UNKNOWN
    license_reference: Optional[str] = None
    validation_run_id: Optional[str] = None
    is_quarantined: bool = False
    quarantine_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["category"] = self.category.value
        d["license_status"] = self.license_status.value
        return d


class DatasetRegistry:
    """
    Registry and versioning engine for all platform datasets.
    """

    def __init__(self):
        self.manifests: Dict[str, List[DatasetManifest]] = {}  # Keyed by dataset_id

    def register_dataset(
        self,
        dataset_id: str,
        category: DatasetCategory,
        vendor: str,
        product_name: str,
        underlying: str,
        frequency: str,
        coverage_start: str,
        coverage_end: str,
        total_records: int,
        source_file: str,
        source_checksum: str,
        schema_version: str = "phase13_v1",
        transformation_version: str = "raw_tape_v1",
        validation_version: str = "val_v1",
        license_status: LicenseStatus = LicenseStatus.LICENSE_UNKNOWN,
        license_reference: Optional[str] = None,
        validation_run_id: Optional[str] = None,
    ) -> DatasetManifest:
        """
        Registers a dataset with content-based versioning and identical checksum detection.
        """
        existing_versions = self.manifests.get(dataset_id, [])

        # Check for identical checksum (content duplicate)
        for existing in existing_versions:
            if existing.source_checksum == source_checksum:
                # Content is identical, return existing version without creating duplicate
                return existing

        # New version number
        version_num = len(existing_versions) + 1
        version_str = f"v{version_num}"

        # Test fixture contamination check
        is_quarantined = False
        quarantine_reason = None
        if category == DatasetCategory.PRODUCTION_DATA:
            fixture_indicators = ["PIT_LEAK_TEST", "TEST_CSV", "FIXTURE", "MOCK", "SYNTHETIC"]
            if any(ind in source_file.upper() or ind in dataset_id.upper() for ind in fixture_indicators):
                is_quarantined = True
                quarantine_reason = "CONTAMINATION_VIOLATION: Test fixture or synthetic data detected in PRODUCTION_DATA."

        manifest = DatasetManifest(
            dataset_id=dataset_id,
            version=version_str,
            category=category,
            vendor=vendor,
            product_name=product_name,
            underlying=underlying,
            frequency=frequency,
            coverage_start=coverage_start,
            coverage_end=coverage_end,
            total_records=total_records,
            source_file=source_file,
            source_checksum=source_checksum,
            schema_version=schema_version,
            transformation_version=transformation_version,
            validation_version=validation_version,
            acquisition_timestamp=datetime.now(timezone.utc).isoformat(),
            license_status=license_status,
            license_reference=license_reference,
            validation_run_id=validation_run_id,
            is_quarantined=is_quarantined,
            quarantine_reason=quarantine_reason,
        )

        if dataset_id not in self.manifests:
            self.manifests[dataset_id] = []
        self.manifests[dataset_id].append(manifest)

        return manifest

    def get_latest_manifest(self, dataset_id: str) -> Optional[DatasetManifest]:
        versions = self.manifests.get(dataset_id, [])
        return versions[-1] if versions else None

    def get_all_manifests(self) -> List[DatasetManifest]:
        all_m = []
        for v_list in self.manifests.values():
            all_m.extend(v_list)
        return all_m

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_registered_datasets": len(self.manifests),
            "datasets": {
                did: [m.to_dict() for m in m_list] for did, m_list in self.manifests.items()
            },
        }
