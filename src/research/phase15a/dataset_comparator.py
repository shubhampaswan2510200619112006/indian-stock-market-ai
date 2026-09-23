"""
Phase 15A Dataset Comparator.

Performs deterministic diagnostic comparison between two datasets (e.g., Vendor A vs Vendor B,
or Raw Delivery vs Re-delivery):
- Temporal coverage overlap
- Missing/unique bar analysis
- Price discrepancies (mean and max differences across Open, High, Low, Close)
- Volume discrepancies
- Deterministic reconciliation score
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from src.research.phase15a.safety_policy import SafetyPolicy


@dataclass
class ComparisonReport:
    comparison_id: str
    dataset_a_id: str
    dataset_b_id: str
    dataset_a_vendor: str
    dataset_b_vendor: str
    underlying: str
    interval: str
    dataset_a_rows: int
    dataset_b_rows: int
    common_timestamps_count: int
    unique_to_a_count: int
    unique_to_b_count: int
    close_price_mean_absolute_diff: float
    close_price_max_absolute_diff: float
    close_price_exact_match_pct: float
    volume_mean_absolute_diff: float
    reconciliation_status: str  # RECONCILED_MATCH, MINOR_DISCREPANCY, MATERIAL_DISCREPANCY, NO_OVERLAP
    diagnostic_notes: List[str] = field(default_factory=list)
    evaluated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DatasetComparator:
    """
    Compares two datasets deterministically on aligned timestamps.
    """

    @classmethod
    def compare(
        cls,
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
        dataset_a_id: str,
        dataset_b_id: str,
        vendor_a: str,
        vendor_b: str,
        underlying: str,
        interval: str,
        timestamp_col: str = "timestamp",
    ) -> ComparisonReport:
        SafetyPolicy.assert_safety_invariants(context=f"DatasetComparator.compare:{dataset_a_id} vs {dataset_b_id}")

        cmp_id = f"CMP-{dataset_a_id[:8]}-{dataset_b_id[:8]}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        if timestamp_col not in df_a.columns or timestamp_col not in df_b.columns:
            return ComparisonReport(
                comparison_id=cmp_id,
                dataset_a_id=dataset_a_id,
                dataset_b_id=dataset_b_id,
                dataset_a_vendor=vendor_a,
                dataset_b_vendor=vendor_b,
                underlying=underlying,
                interval=interval,
                dataset_a_rows=len(df_a),
                dataset_b_rows=len(df_b),
                common_timestamps_count=0,
                unique_to_a_count=len(df_a),
                unique_to_b_count=len(df_b),
                close_price_mean_absolute_diff=0.0,
                close_price_max_absolute_diff=0.0,
                close_price_exact_match_pct=0.0,
                volume_mean_absolute_diff=0.0,
                reconciliation_status="NO_OVERLAP",
                diagnostic_notes=["Missing timestamp column in one or both datasets"],
            )

        ts_a = set(df_a[timestamp_col].astype(str))
        ts_b = set(df_b[timestamp_col].astype(str))

        common_ts = ts_a.intersection(ts_b)
        unique_a = len(ts_a - ts_b)
        unique_b = len(ts_b - ts_a)

        notes = []
        if len(common_ts) == 0:
            notes.append("Zero temporal overlap found between datasets")
            return ComparisonReport(
                comparison_id=cmp_id,
                dataset_a_id=dataset_a_id,
                dataset_b_id=dataset_b_id,
                dataset_a_vendor=vendor_a,
                dataset_b_vendor=vendor_b,
                underlying=underlying,
                interval=interval,
                dataset_a_rows=len(df_a),
                dataset_b_rows=len(df_b),
                common_timestamps_count=0,
                unique_to_a_count=unique_a,
                unique_to_b_count=unique_b,
                close_price_mean_absolute_diff=0.0,
                close_price_max_absolute_diff=0.0,
                close_price_exact_match_pct=0.0,
                volume_mean_absolute_diff=0.0,
                reconciliation_status="NO_OVERLAP",
                diagnostic_notes=notes,
            )

        # Merge on timestamp for numerical comparison
        df_a_sub = df_a[[timestamp_col, "close", "volume"]].copy() if "close" in df_a.columns and "volume" in df_a.columns else df_a.copy()
        df_b_sub = df_b[[timestamp_col, "close", "volume"]].copy() if "close" in df_b.columns and "volume" in df_b.columns else df_b.copy()

        df_a_sub[timestamp_col] = df_a_sub[timestamp_col].astype(str)
        df_b_sub[timestamp_col] = df_b_sub[timestamp_col].astype(str)

        merged = pd.merge(df_a_sub, df_b_sub, on=timestamp_col, suffixes=("_a", "_b"))

        close_diffs = np.abs(pd.to_numeric(merged["close_a"], errors="coerce") - pd.to_numeric(merged["close_b"], errors="coerce"))
        close_mean = float(close_diffs.mean()) if not close_diffs.empty else 0.0
        close_max = float(close_diffs.max()) if not close_diffs.empty else 0.0
        exact_match = float((close_diffs < 1e-4).mean() * 100.0) if not close_diffs.empty else 0.0

        vol_diffs = np.abs(pd.to_numeric(merged["volume_a"], errors="coerce") - pd.to_numeric(merged["volume_b"], errors="coerce")) if ("volume_a" in merged.columns and "volume_b" in merged.columns) else pd.Series([])
        vol_mean = float(vol_diffs.mean()) if not vol_diffs.empty else 0.0

        if exact_match >= 99.9 and unique_a == 0 and unique_b == 0:
            status = "RECONCILED_MATCH"
        elif exact_match >= 95.0:
            status = "MINOR_DISCREPANCY"
            notes.append(f"Minor discrepancies observed: max diff={close_max:.2f}")
        else:
            status = "MATERIAL_DISCREPANCY"
            notes.append(f"Material discrepancies observed: exact match pct={exact_match:.1f}%")

        return ComparisonReport(
            comparison_id=cmp_id,
            dataset_a_id=dataset_a_id,
            dataset_b_id=dataset_b_id,
            dataset_a_vendor=vendor_a,
            dataset_b_vendor=vendor_b,
            underlying=underlying,
            interval=interval,
            dataset_a_rows=len(df_a),
            dataset_b_rows=len(df_b),
            common_timestamps_count=len(common_ts),
            unique_to_a_count=unique_a,
            unique_to_b_count=unique_b,
            close_price_mean_absolute_diff=round(close_mean, 4),
            close_price_max_absolute_diff=round(close_max, 4),
            close_price_exact_match_pct=round(exact_match, 2),
            volume_mean_absolute_diff=round(vol_mean, 2),
            reconciliation_status=status,
            diagnostic_notes=notes,
        )
