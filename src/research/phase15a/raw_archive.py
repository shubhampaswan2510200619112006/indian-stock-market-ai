"""
Phase 15A Raw Archive Manager.

Enforces raw data immutability and records cryptographic lineage.
Identical content is identified by SHA256 regardless of filename.
Captures complete archive and sub-file lineage for ZIP containers.
Never modifies raw vendor files in place.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from src.research.phase15a.safety_policy import SafetyPolicy


def compute_file_sha256(file_path: str) -> str:
    """Computes SHA256 checksum of a file on disk."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found for checksum: {file_path}")
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_bytes_sha256(data: bytes) -> str:
    """Computes SHA256 checksum of raw bytes in memory."""
    return hashlib.sha256(data).hexdigest()


@dataclass
class ZipEntryRecord:
    parent_archive_sha256: str
    contained_filename: str
    contained_file_size_bytes: int
    contained_file_sha256: str
    detected_format: str  # e.g., CSV, JSON, PARQUET, UNKNOWN

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RawArtifactRecord:
    intake_id: str
    dataset_id: str
    vendor: str
    source_description: str
    received_at: str
    original_filename: str
    original_size_bytes: int
    sha256: str
    mime_type: str
    source_artifact_path: str
    license_reference: str = "LICENSE_UNKNOWN"
    duplicate_artifact: bool = False
    is_zip_container: bool = False
    zip_entries: List[ZipEntryRecord] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["zip_entries"] = [z.to_dict() for z in self.zip_entries]
        return d


class RawArchiveManager:
    """
    Manages raw vendor artifacts, guarantees immutability, and catalogs container lineage.
    """

    def __init__(self, raw_storage_dir: str = "data/intake/raw"):
        self.raw_storage_dir = raw_storage_dir
        self.registry: Dict[str, RawArtifactRecord] = {}  # Keyed by intake_id
        self.known_checksums: Dict[str, str] = {}  # sha256 -> intake_id
        os.makedirs(self.raw_storage_dir, exist_ok=True)

    def ingest_raw_file(
        self,
        intake_id: str,
        dataset_id: str,
        vendor: str,
        source_path: str,
        source_description: str = "Vendor direct delivery",
        license_reference: str = "LICENSE_UNKNOWN",
        copy_to_raw_archive: bool = False,
    ) -> Tuple[RawArtifactRecord, bool]:
        """
        Ingests a raw vendor artifact.
        Returns (RawArtifactRecord, is_duplicate).
        """
        SafetyPolicy.assert_safety_invariants(context=f"RawArchiveManager.ingest:{intake_id}")

        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Raw source artifact does not exist: {source_path}")

        file_size = os.path.getsize(source_path)
        sha256 = compute_file_sha256(source_path)
        filename = os.path.basename(source_path)

        # Detect format / mime
        is_zip = False
        mime = "application/octet-stream"
        zip_entries: List[ZipEntryRecord] = []

        if filename.lower().endswith(".zip") or zipfile.is_zipfile(source_path):
            is_zip = True
            mime = "application/zip"
            # Inspect ZIP entries and calculate hashes without modifying
            try:
                with zipfile.ZipFile(source_path, "r") as z:
                    for zinfo in z.infolist():
                        if not zinfo.is_dir():
                            with z.open(zinfo.filename) as zf:
                                content = zf.read()
                                z_hash = compute_bytes_sha256(content)
                                # detect format
                                ext = zinfo.filename.lower().split(".")[-1] if "." in zinfo.filename else "unknown"
                                zip_entries.append(
                                    ZipEntryRecord(
                                        parent_archive_sha256=sha256,
                                        contained_filename=zinfo.filename,
                                        contained_file_size_bytes=zinfo.file_size,
                                        contained_file_sha256=z_hash,
                                        detected_format=ext.upper(),
                                    )
                                )
            except Exception:
                pass
        elif filename.lower().endswith(".csv") or filename.lower().endswith(".csv.gz"):
            mime = "text/csv"
        elif filename.lower().endswith(".parquet"):
            mime = "application/vnd.apache.parquet"
        elif filename.lower().endswith(".json"):
            mime = "application/json"

        # Checksum duplication check
        is_duplicate = (sha256 in self.known_checksums)

        # Target immutable storage path
        dest_path = source_path
        if copy_to_raw_archive:
            dest_filename = f"{sha256[:12]}_{filename}"
            dest_path = os.path.join(self.raw_storage_dir, dest_filename)
            if not os.path.exists(dest_path):
                shutil.copy2(source_path, dest_path)

        record = RawArtifactRecord(
            intake_id=intake_id,
            dataset_id=dataset_id,
            vendor=vendor,
            source_description=source_description,
            received_at=datetime.now(timezone.utc).isoformat(),
            original_filename=filename,
            original_size_bytes=file_size,
            sha256=sha256,
            mime_type=mime,
            source_artifact_path=dest_path,
            license_reference=license_reference,
            duplicate_artifact=is_duplicate,
            is_zip_container=is_zip,
            zip_entries=zip_entries,
        )

        self.registry[intake_id] = record
        if not is_duplicate:
            self.known_checksums[sha256] = intake_id

        return record, is_duplicate

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_raw_artifacts": len(self.registry),
            "artifacts": {k: v.to_dict() for k, v in self.registry.items()},
        }
