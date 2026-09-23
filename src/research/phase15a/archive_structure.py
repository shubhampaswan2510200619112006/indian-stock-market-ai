"""
Phase 15A Archive Structure Manager.

Enforces deterministic archive structure:
- data/intake/raw/          (immutable vendor originals)
- data/intake/normalized/   (deterministically normalized standard representations)
- data/intake/derived/      (deterministically derived representations, e.g. 5m from 1m)
- data/intake/certified/    (metadata pointers to successfully certified datasets)
- data/intake/quarantine/   (isolated fixtures or corrupted vendor deliveries)

Enforces fixture isolation and path security across all tiers.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from src.research.phase15a.safety_policy import SafetyPolicy


@dataclass
class ArchiveTierPaths:
    raw_dir: str
    normalized_dir: str
    derived_dir: str
    certified_dir: str
    quarantine_dir: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


class ArchiveStructureManager:
    """
    Manages deterministic directory structure and tier routing for Phase 15A.
    """

    def __init__(self, base_intake_dir: str = "data/intake"):
        self.base_intake_dir = base_intake_dir
        self.raw_dir = os.path.join(base_intake_dir, "raw")
        self.normalized_dir = os.path.join(base_intake_dir, "normalized")
        self.derived_dir = os.path.join(base_intake_dir, "derived")
        self.certified_dir = os.path.join(base_intake_dir, "certified")
        self.quarantine_dir = os.path.join(base_intake_dir, "quarantine")

    def initialize_directories(self) -> ArchiveTierPaths:
        """Ensures all 5 deterministic intake directories exist."""
        SafetyPolicy.assert_safety_invariants(context="ArchiveStructureManager.initialize_directories")
        for path in [
            self.raw_dir,
            self.normalized_dir,
            self.derived_dir,
            self.certified_dir,
            self.quarantine_dir,
        ]:
            os.makedirs(path, exist_ok=True)

        return ArchiveTierPaths(
            raw_dir=self.raw_dir,
            normalized_dir=self.normalized_dir,
            derived_dir=self.derived_dir,
            certified_dir=self.certified_dir,
            quarantine_dir=self.quarantine_dir,
        )

    def get_paths(self) -> ArchiveTierPaths:
        return ArchiveTierPaths(
            raw_dir=self.raw_dir,
            normalized_dir=self.normalized_dir,
            derived_dir=self.derived_dir,
            certified_dir=self.certified_dir,
            quarantine_dir=self.quarantine_dir,
        )

    def quarantine_artifact(self, source_path: str, reason: str) -> str:
        """
        Safely copies or moves an artifact to quarantine without executing it.
        Returns the quarantined destination path.
        """
        SafetyPolicy.assert_safety_invariants(context=f"ArchiveStructureManager.quarantine:{source_path}")
        self.initialize_directories()
        basename = os.path.basename(source_path)
        dest_path = os.path.join(self.quarantine_dir, f"QUARANTINED_{basename}")
        shutil.copy2(source_path, dest_path)
        return dest_path
