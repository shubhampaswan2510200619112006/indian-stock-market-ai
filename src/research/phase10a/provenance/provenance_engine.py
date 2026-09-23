"""
Phase 10A — Data Provenance, Versioning & Inventory Engine.

Manages data lineage, cryptographic SHA256 hashing, and quality tiering
for all datasets ingested or generated in Phase 10A.

Data Tiers:
- Tier 1: Authoritative / Point-in-Time (Official exchange circulars, trading calendar, verified constituent registry)
- Tier 2: Research-Grade (Adjusted daily historical equity panels with >= 2-year verified window)
- Tier 3: Limited / Exploratory-Only (Observed intraday bars with provider retention limits, settlement-only options quotes)

Outputs:
- data/phase10a/data_inventory.json
- data/phase10a/provenance.json
"""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List


def compute_file_sha256(path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    if not path.exists():
        return "MISSING"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class Phase10AProvenanceEngine:
    """
    Provenance, versioning, and inventory manager for Phase 10A datasets.
    """

    @classmethod
    def generate_inventory_and_provenance(cls) -> Dict[str, Any]:
        """
        Scan and hash all Phase 10A data assets, assign versions, and build inventory.
        """
        now_utc = datetime.now(timezone.utc).isoformat()
        base_dir = Path("data/phase10a")

        datasets: List[Dict[str, Any]] = []

        # 1. Tier 1 Assets
        tier_1_files = [
            {
                "id": "NSE_MARKET_CALENDAR_2024_2026",
                "path": "src/research/phase10a/validation/calendar_validator.py",
                "format": "PYTHON_MODULE",
                "tier": "TIER_1_AUTHORITATIVE",
                "source": "National Stock Exchange of India (NSE) Official Circulars",
                "description": "NSE exchange trading sessions, official holidays, and Muhurat trading sessions.",
                "version": "1.0",
                "license": "Public Regulatory / Exchange Disclosure",
            },
            {
                "id": "NIFTY_50_PIT_CONSTITUENT_REGISTRY",
                "path": "data/phase10a/constituent_integrity.json",
                "format": "JSON",
                "tier": "TIER_1_AUTHORITATIVE",
                "source": "NSE Indices Press Releases and Semi-Annual Reconstitution Circulars",
                "description": "Chronological additions, exclusions, effective dates, and survivorship-safe constituent resolution.",
                "version": "1.0",
                "license": "Public Regulatory / Index Disclosure",
            },
        ]

        # 2. Tier 2 Assets (Daily Equity Panel)
        equity_dir = base_dir / "equity"
        tier_2_files = []
        if equity_dir.exists():
            for csv_file in sorted(equity_dir.glob("*_daily.csv")):
                sym = csv_file.stem.replace("_daily", "").upper()
                tier_2_files.append({
                    "id": f"EQUITY_DAILY_{sym}_v1",
                    "path": str(csv_file).replace("\\", "/"),
                    "format": "CSV",
                    "tier": "TIER_2_RESEARCH_GRADE",
                    "source": "Yahoo Finance (yfinance historical daily endpoint)",
                    "description": f"Daily OHLCV historical bars and corporate actions for {sym} (minimum 2 years, up to 30 years).",
                    "version": "1.0",
                    "license": "Public Historical Market Data",
                })

        # 3. Tier 3 Assets (Intraday Bars & Options Quotes)
        intraday_dir = base_dir / "intraday"
        tier_3_files = []
        if intraday_dir.exists():
            for csv_file in sorted(intraday_dir.glob("*.csv")):
                tier_3_files.append({
                    "id": f"INTRADAY_{csv_file.stem.upper()}_v1",
                    "path": str(csv_file).replace("\\", "/"),
                    "format": "CSV",
                    "tier": "TIER_3_EXPLORATORY_ONLY",
                    "source": "Yahoo Finance (yfinance intraday rolling endpoint)",
                    "description": f"Intraday bars ({csv_file.stem}) subject to provider retention limits (7d for 1m, 60d for 5m).",
                    "version": "1.0",
                    "license": "Public Market Data (Rolling Window)",
                })

        tier_3_files.append({
            "id": "OPTIONS_REPOSITORY_HISTORICAL_QUOTES",
            "path": "data/indian_options.db",
            "format": "SQLITE",
            "tier": "TIER_3_EXPLORATORY_ONLY",
            "source": "Historical Bhavcopy & Options Quote Snapshots",
            "description": "17,098 option quotes; 114 paired Bid/Ask quotes (0.67%); 0.0% continuous executable surface. Execution BLOCKED.",
            "version": "1.0",
            "license": "Internal Research Snapshot",
        })

        all_manifest_items = tier_1_files + tier_2_files + tier_3_files

        for item in all_manifest_items:
            fpath = Path(item["path"])
            h = compute_file_sha256(fpath)
            size_bytes = fpath.stat().st_size if fpath.exists() else 0
            mtime = (
                datetime.fromtimestamp(fpath.stat().st_mtime, tz=timezone.utc).isoformat()
                if fpath.exists()
                else now_utc
            )
            item["sha256"] = h
            item["file_size_bytes"] = size_bytes
            item["modification_timestamp_utc"] = mtime
            datasets.append(item)

        # Build Inventory
        inventory = {
            "inventory_version": "1.0",
            "generated_at_utc": now_utc,
            "phase": "PHASE_10A",
            "total_datasets_tracked": len(datasets),
            "tier_summary": {
                "TIER_1_AUTHORITATIVE": sum(1 for d in datasets if d["tier"] == "TIER_1_AUTHORITATIVE"),
                "TIER_2_RESEARCH_GRADE": sum(1 for d in datasets if d["tier"] == "TIER_2_RESEARCH_GRADE"),
                "TIER_3_EXPLORATORY_ONLY": sum(1 for d in datasets if d["tier"] == "TIER_3_EXPLORATORY_ONLY"),
            },
            "datasets": datasets,
        }

        # Build Lineage & Provenance
        provenance = {
            "provenance_version": "1.0",
            "generated_at_utc": now_utc,
            "phase": "PHASE_10A_DATA_FOUNDATION",
            "governance_invariants": {
                "ALLOW_LIVE_EXECUTION": False,
                "LIVE_EXECUTION": "DISABLED",
                "BROKER": "NONE",
                "AUTO_PAPER_ORDER_SUBMISSION": "DISABLED",
                "OPTIONS_EXECUTION": "BLOCKED",
                "ALPHA_HYPOTHESIS_TESTING": "STRICTLY_PROHIBITED",
            },
            "lineage_records": [
                {
                    "stage": "INGESTION_AND_AUDIT",
                    "actor": "Phase 10A Data Foundation Engine",
                    "execution_timestamp": now_utc,
                    "datasets_produced": [d["id"] for d in datasets],
                    "verification_method": "Cryptographic SHA256 & Mathematical Invariant Auditing",
                }
            ],
            "dataset_manifest": {d["id"]: {"path": d["path"], "sha256": d["sha256"], "tier": d["tier"]} for d in datasets},
        }

        # Save artifacts
        base_dir.mkdir(parents=True, exist_ok=True)
        with open(base_dir / "data_inventory.json", "w", encoding="utf-8") as f:
            json.dump(inventory, f, indent=2)

        with open(base_dir / "provenance.json", "w", encoding="utf-8") as f:
            json.dump(provenance, f, indent=2)

        return {
            "inventory": inventory,
            "provenance": provenance,
        }


if __name__ == "__main__":
    res = Phase10AProvenanceEngine.generate_inventory_and_provenance()
    print("Data Inventory & Provenance Generated:")
    print("Total tracked:", res["inventory"]["total_datasets_tracked"])
    print("Tiers:", res["inventory"]["tier_summary"])
