"""
Phase 15A Multi-File Dataset Tracker.

Tracks multi-file dataset groups:
- dataset_group_id, artifact_id, sequence, coverage_start, coverage_end, file_count
Never silently concatenates datasets with mismatched schemas or corrupts individual chunk lineage.
Provides boundary continuity analysis between consecutive files in a group.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

from src.research.phase15a.safety_policy import SafetyPolicy


@dataclass
class FileChunkRecord:
    artifact_id: str
    sequence_number: int
    file_path: str
    sha256: str
    total_rows: int
    coverage_start: Optional[str] = None
    coverage_end: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MultiFileGroupRecord:
    dataset_group_id: str
    underlying: str
    interval: str
    vendor: str
    total_files: int
    total_rows: int
    overall_coverage_start: Optional[str]
    overall_coverage_end: Optional[str]
    is_schema_consistent: bool
    has_boundary_overlaps: bool
    has_boundary_gaps: bool
    chunks: List[FileChunkRecord] = field(default_factory=list)
    schema_columns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["chunks"] = [c.to_dict() for c in self.chunks]
        return d


class MultiFileDatasetTracker:
    """
    Manages and validates chunked multi-file dataset deliveries.
    """

    def __init__(self):
        self.groups: Dict[str, MultiFileGroupRecord] = {}

    def register_group(
        self,
        dataset_group_id: str,
        underlying: str,
        interval: str,
        vendor: str,
        file_paths_in_order: List[str],
        timestamp_col: str = "timestamp",
    ) -> MultiFileGroupRecord:
        SafetyPolicy.assert_safety_invariants(context=f"MultiFileDatasetTracker.register:{dataset_group_id}")

        chunks: List[FileChunkRecord] = []
        total_rows = 0
        is_schema_consistent = True
        reference_columns: Optional[List[str]] = None
        has_boundary_overlaps = False
        has_boundary_gaps = False

        overall_start: Optional[str] = None
        overall_end: Optional[str] = None
        prev_end: Optional[str] = None

        for idx, fpath in enumerate(file_paths_in_order, start=1):
            if not os.path.exists(fpath):
                raise FileNotFoundError(f"Chunk file not found: {fpath}")

            # Read sample or full header
            df = pd.read_csv(fpath) if fpath.endswith(".csv") else pd.read_parquet(fpath)
            cols = list(df.columns)
            if reference_columns is None:
                reference_columns = cols
            elif set(cols) != set(reference_columns):
                is_schema_consistent = False

            rows = len(df)
            total_rows += rows

            c_start = None
            c_end = None
            if timestamp_col in df.columns and rows > 0:
                c_start = str(df[timestamp_col].iloc[0])
                c_end = str(df[timestamp_col].iloc[-1])

                if overall_start is None:
                    overall_start = c_start
                overall_end = c_end

                if prev_end is not None:
                    if c_start < prev_end:
                        has_boundary_overlaps = True
                prev_end = c_end

            import hashlib
            h = hashlib.sha256()
            with open(fpath, "rb") as f:
                for b in iter(lambda: f.read(65536), b""):
                    h.update(b)
            f_sha256 = h.hexdigest()

            chunk = FileChunkRecord(
                artifact_id=f"CHUNK-{dataset_group_id}-{idx:03d}",
                sequence_number=idx,
                file_path=fpath,
                sha256=f_sha256,
                total_rows=rows,
                coverage_start=c_start,
                coverage_end=c_end,
            )
            chunks.append(chunk)

        rec = MultiFileGroupRecord(
            dataset_group_id=dataset_group_id,
            underlying=underlying,
            interval=interval,
            vendor=vendor,
            total_files=len(chunks),
            total_rows=total_rows,
            overall_coverage_start=overall_start,
            overall_coverage_end=overall_end,
            is_schema_consistent=is_schema_consistent,
            has_boundary_overlaps=has_boundary_overlaps,
            has_boundary_gaps=has_boundary_gaps,
            chunks=chunks,
            schema_columns=reference_columns or [],
        )

        self.groups[dataset_group_id] = rec
        return rec
