"""
Phase 15A Safe File Inspector.

Safely inspects multi-format dataset artifacts:
- CSV, CSV.GZ, PARQUET, ZIP, JSON
Detects corrupted or truncated files safely without executing vendor binaries or scripts.
Extracts schema, row count estimates, byte size, detected encoding, and sample records.
"""

from __future__ import annotations

import csv
import gzip
import json
import os
import zipfile
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from src.research.phase15a.safety_policy import SafetyPolicy


class CorruptedFileError(Exception):
    """Raised when a file cannot be parsed or is corrupted."""
    pass


@dataclass
class FileInspectionResult:
    file_path: str
    detected_format: str  # CSV, CSV_GZ, PARQUET, ZIP, JSON, CORRUPTED, UNKNOWN
    file_size_bytes: int
    is_corrupted: bool
    corruption_reason: Optional[str] = None
    columns: List[str] = field(default_factory=list)
    estimated_rows: int = 0
    sample_rows: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SafeFileInspector:
    """
    Safely inspects file contents without code execution risk.
    """

    @classmethod
    def inspect_file(cls, file_path: str) -> FileInspectionResult:
        SafetyPolicy.assert_safety_invariants(context=f"SafeFileInspector.inspect:{file_path}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return FileInspectionResult(
                file_path=file_path,
                detected_format="CORRUPTED",
                file_size_bytes=0,
                is_corrupted=True,
                corruption_reason="File is empty (0 bytes)",
            )

        lower_path = file_path.lower()

        # 1. ZIP Inspection
        if lower_path.endswith(".zip"):
            return cls._inspect_zip(file_path, file_size)

        # 2. GZIP / CSV.GZ Inspection
        if lower_path.endswith(".csv.gz") or lower_path.endswith(".gz"):
            return cls._inspect_csv_gz(file_path, file_size)

        # 3. PARQUET Inspection
        if lower_path.endswith(".parquet"):
            return cls._inspect_parquet(file_path, file_size)

        # 4. JSON Inspection
        if lower_path.endswith(".json"):
            return cls._inspect_json(file_path, file_size)

        # 5. CSV Inspection
        return cls._inspect_csv(file_path, file_size)

    @classmethod
    def _inspect_zip(cls, file_path: str, file_size: int) -> FileInspectionResult:
        try:
            if not zipfile.is_zipfile(file_path):
                return FileInspectionResult(
                    file_path=file_path,
                    detected_format="CORRUPTED",
                    file_size_bytes=file_size,
                    is_corrupted=True,
                    corruption_reason="Invalid or truncated ZIP archive header",
                )

            with zipfile.ZipFile(file_path, "r") as z:
                bad_file = z.testzip()
                if bad_file is not None:
                    return FileInspectionResult(
                        file_path=file_path,
                        detected_format="CORRUPTED",
                        file_size_bytes=file_size,
                        is_corrupted=True,
                        corruption_reason=f"CRC check failed for ZIP entry: {bad_file}",
                    )
                infolist = z.infolist()
                entries = [
                    {
                        "filename": info.filename,
                        "file_size": info.file_size,
                        "compress_size": info.compress_size,
                    }
                    for info in infolist
                ]
                return FileInspectionResult(
                    file_path=file_path,
                    detected_format="ZIP",
                    file_size_bytes=file_size,
                    is_corrupted=False,
                    columns=["contained_files"],
                    estimated_rows=len(infolist),
                    metadata={"contained_files": entries},
                )
        except Exception as e:
            return FileInspectionResult(
                file_path=file_path,
                detected_format="CORRUPTED",
                file_size_bytes=file_size,
                is_corrupted=True,
                corruption_reason=f"ZIP inspection error: {str(e)}",
            )

    @classmethod
    def _inspect_csv_gz(cls, file_path: str, file_size: int) -> FileInspectionResult:
        try:
            with gzip.open(file_path, "rt", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if not header:
                    return FileInspectionResult(
                        file_path=file_path,
                        detected_format="CORRUPTED",
                        file_size_bytes=file_size,
                        is_corrupted=True,
                        corruption_reason="CSV.GZ has no readable header or rows",
                    )
                rows = []
                count = 0
                for row in reader:
                    count += 1
                    if len(rows) < 5:
                        rows.append(dict(zip(header, row)))
                return FileInspectionResult(
                    file_path=file_path,
                    detected_format="CSV_GZ",
                    file_size_bytes=file_size,
                    is_corrupted=False,
                    columns=[str(c).strip() for c in header],
                    estimated_rows=count,
                    sample_rows=rows,
                )
        except Exception as e:
            return FileInspectionResult(
                file_path=file_path,
                detected_format="CORRUPTED",
                file_size_bytes=file_size,
                is_corrupted=True,
                corruption_reason=f"CSV.GZ decompression or parse error: {str(e)}",
            )

    @classmethod
    def _inspect_parquet(cls, file_path: str, file_size: int) -> FileInspectionResult:
        try:
            # Check magic bytes 'PAR1'
            with open(file_path, "rb") as f:
                magic_head = f.read(4)
                if magic_head != b"PAR1":
                    return FileInspectionResult(
                        file_path=file_path,
                        detected_format="CORRUPTED",
                        file_size_bytes=file_size,
                        is_corrupted=True,
                        corruption_reason="Invalid Parquet magic bytes",
                    )
            import pandas as pd
            df = pd.read_parquet(file_path)
            return FileInspectionResult(
                file_path=file_path,
                detected_format="PARQUET",
                file_size_bytes=file_size,
                is_corrupted=False,
                columns=[str(c) for c in df.columns],
                estimated_rows=len(df),
                sample_rows=df.head(5).to_dict(orient="records"),
            )
        except Exception as e:
            return FileInspectionResult(
                file_path=file_path,
                detected_format="CORRUPTED",
                file_size_bytes=file_size,
                is_corrupted=True,
                corruption_reason=f"Parquet parse error: {str(e)}",
            )

    @classmethod
    def _inspect_json(cls, file_path: str, file_size: int) -> FileInspectionResult:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                cols = list(data[0].keys()) if len(data) > 0 and isinstance(data[0], dict) else []
                return FileInspectionResult(
                    file_path=file_path,
                    detected_format="JSON",
                    file_size_bytes=file_size,
                    is_corrupted=False,
                    columns=cols,
                    estimated_rows=len(data),
                    sample_rows=data[:5] if isinstance(data[0], dict) else [],
                )
            elif isinstance(data, dict):
                return FileInspectionResult(
                    file_path=file_path,
                    detected_format="JSON",
                    file_size_bytes=file_size,
                    is_corrupted=False,
                    columns=list(data.keys()),
                    estimated_rows=1,
                    metadata={"keys_count": len(data)},
                )
            return FileInspectionResult(
                file_path=file_path,
                detected_format="JSON",
                file_size_bytes=file_size,
                is_corrupted=False,
            )
        except Exception as e:
            return FileInspectionResult(
                file_path=file_path,
                detected_format="CORRUPTED",
                file_size_bytes=file_size,
                is_corrupted=True,
                corruption_reason=f"JSON parse error: {str(e)}",
            )

    @classmethod
    def _inspect_csv(cls, file_path: str, file_size: int) -> FileInspectionResult:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                # Read initial lines
                lines = [f.readline() for _ in range(50)]
            if not lines or not lines[0].strip():
                return FileInspectionResult(
                    file_path=file_path,
                    detected_format="CORRUPTED",
                    file_size_bytes=file_size,
                    is_corrupted=True,
                    corruption_reason="CSV file is empty or blank",
                )

            # Use csv.reader on lines
            reader = csv.reader(lines)
            header = next(reader, None)
            if not header:
                return FileInspectionResult(
                    file_path=file_path,
                    detected_format="CORRUPTED",
                    file_size_bytes=file_size,
                    is_corrupted=True,
                    corruption_reason="No CSV header detected",
                )

            sample_rows = []
            for row in reader:
                if row and len(sample_rows) < 5:
                    sample_rows.append(dict(zip(header, row)))

            # Count total lines efficiently
            with open(file_path, "rb") as f:
                total_lines = sum(1 for _ in f)

            return FileInspectionResult(
                file_path=file_path,
                detected_format="CSV",
                file_size_bytes=file_size,
                is_corrupted=False,
                columns=[str(c).strip() for c in header],
                estimated_rows=max(0, total_lines - 1),
                sample_rows=sample_rows,
            )
        except Exception as e:
            return FileInspectionResult(
                file_path=file_path,
                detected_format="CORRUPTED",
                file_size_bytes=file_size,
                is_corrupted=True,
                corruption_reason=f"CSV read error: {str(e)}",
            )
