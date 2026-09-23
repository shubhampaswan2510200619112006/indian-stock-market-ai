"""
Phase 15A Normalization Engine.

Enforces deterministic normalization with cryptographic lineage tracking.
Identical input + identical transformation version produces identical normalized output.
Records complete input_sha256, output_sha256, transformation name, and version lineage.

CRITICAL INVARIANT (Correction 5):
NO SILENT REPAIR. Never interpolate missing bars, infer quotes, smooth prices,
repair gaps, alter timestamps to hide problems, or manufacture Bid/Ask values.
Pass detected defects to Phase 14 unchanged for deterministic certification diagnostics.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.research.phase15a.safety_policy import SafetyPolicy


def compute_file_hash(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class TransformationAuditRecord:
    transformation_id: str
    transformation_name: str
    transformation_version: str
    input_sha256: str
    output_sha256: str
    source_file: str
    output_file: str
    executed_at: str
    input_rows: int
    output_rows: int
    column_mapping: Dict[str, str] = field(default_factory=dict)
    silent_repair_checked: bool = True
    repaired_interpolated_bars_count: int = 0  # Strictly 0 by policy

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class NormalizationEngine:
    """
    Deterministically normalizes tabular market data without performing silent repairs.
    """

    TRANSFORMATION_VERSION: str = "v1.0.0_canonical"

    # Known column aliases for canonical mapping
    COLUMN_ALIASES: Dict[str, str] = {
        "datetime": "timestamp",
        "date_time": "timestamp",
        "date": "date",
        "time": "time",
        "<date>": "date",
        "<time>": "time",
        "<open>": "open",
        "<high>": "high",
        "<low>": "low",
        "<close>": "close",
        "<volume>": "volume",
        "<vol>": "volume",
        "<oi>": "oi",
        "<openinterest>": "oi",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
        "vol": "volume",
        "oi": "oi",
        "open_interest": "oi",
        "openinterest": "oi",
        "bid": "bid",
        "ask": "ask",
        "best_bid": "bid",
        "best_ask": "ask",
        "bid_price": "bid",
        "ask_price": "ask",
        "strike": "strike",
        "option_type": "option_type",
        "expiry": "expiry",
        "symbol": "symbol",
        "ticker": "symbol",
    }

    @classmethod
    def normalize_file(
        cls,
        input_path: str,
        output_path: str,
        transformation_name: str = "CANONICAL_OHLCV_NORMALIZATION",
    ) -> Tuple[pd.DataFrame, TransformationAuditRecord]:
        SafetyPolicy.assert_safety_invariants(context=f"NormalizationEngine.normalize_file:{input_path}")

        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        input_sha256 = compute_file_hash(input_path)

        # Read input safely
        lower = input_path.lower()
        if lower.endswith(".parquet"):
            df = pd.read_parquet(input_path)
        else:
            df = pd.read_csv(input_path)

        input_rows = len(df)
        col_mapping: Dict[str, str] = {}

        # 1. Map columns deterministically
        renamed_cols = {}
        for col in df.columns:
            clean_col = str(col).strip().lower()
            if clean_col in cls.COLUMN_ALIASES:
                target = cls.COLUMN_ALIASES[clean_col]
                renamed_cols[col] = target
                col_mapping[str(col)] = target
            else:
                renamed_cols[col] = clean_col
                col_mapping[str(col)] = clean_col

        df = df.rename(columns=renamed_cols)

        # 2. Combine date + time into timestamp if separate
        if "timestamp" not in df.columns and "date" in df.columns and "time" in df.columns:
            # Combine without altering data
            df["timestamp"] = df["date"].astype(str).str.strip() + " " + df["time"].astype(str).str.strip()
            col_mapping["date+time_combined"] = "timestamp"

        # Strictly DO NOT interpolate, DO NOT fill missing bars, DO NOT smooth prices, DO NOT synthesize bid/ask
        # Output rows MUST strictly equal input rows
        output_rows = len(df)
        if output_rows != input_rows:
            raise ValueError(
                f"Row count mismatch in normalization: input={input_rows}, output={output_rows}. "
                "Silent filtering or bar creation is strictly prohibited."
            )

        # Ensure directory exists and write deterministically
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        # Use line_terminator='\n' or index=False for exact bit-for-bit determinism
        df.to_csv(output_path, index=False, lineterminator="\n")

        output_sha256 = compute_file_hash(output_path)

        audit_record = TransformationAuditRecord(
            transformation_id=f"NORM-{input_sha256[:10]}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            transformation_name=transformation_name,
            transformation_version=cls.TRANSFORMATION_VERSION,
            input_sha256=input_sha256,
            output_sha256=output_sha256,
            source_file=input_path,
            output_file=output_path,
            executed_at=datetime.now(timezone.utc).isoformat(),
            input_rows=input_rows,
            output_rows=output_rows,
            column_mapping=col_mapping,
            silent_repair_checked=True,
            repaired_interpolated_bars_count=0,
        )

        return df, audit_record
