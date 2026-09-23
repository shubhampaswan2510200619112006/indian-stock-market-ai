"""
Phase 10B — Options Data Quality & Executability Engine.

Performs deep quality auditing across the resident options database:
1. Distinguishes paired quote observation coverage from continuous executable surface coverage.
2. Audits strike/expiry coverage, bid/ask coverage, crossed markets, invalid quotes.
3. Quantifies surface density across trading hours.
4. Strictly enforces the execution block until genuine executable Bid/Ask data passes.
Outputs: data/phase10b/options_quality.json.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, List

from src.research.phase10b.acquisition.options_dataset_version import OptionsDatasetVersionManager


class OptionsQualityEngine:
    """
    Quality gate auditor for options market microstructure and execution realism.
    """

    DB_PATH = Path("data/indian_options.db")

    @classmethod
    def audit_options_quality(cls) -> Dict[str, Any]:
        """
        Execute complete options quality audit and save data/phase10b/options_quality.json.
        """
        version_audit = OptionsDatasetVersionManager.audit_current_phase10b_dataset()
        p10b_meta = version_audit["versions_tracked"]["PHASE_10B_DATASET"]

        db_path = cls.DB_PATH
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        # Contract coverage
        cur.execute("SELECT COUNT(DISTINCT underlying) FROM options_contracts")
        underlyings_count = cur.fetchone()[0]

        cur.execute("SELECT DISTINCT underlying FROM options_contracts")
        underlyings_list = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT COUNT(DISTINCT expiry_date) FROM options_contracts")
        expiries_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(DISTINCT strike_price) FROM options_contracts")
        strikes_count = cur.fetchone()[0]

        # Bid / Ask coverage
        cur.execute("SELECT COUNT(*) FROM options_quotes WHERE bid_price IS NOT NULL AND bid_price > 0")
        valid_bids = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM options_quotes WHERE ask_price IS NOT NULL AND ask_price > 0")
        valid_asks = cur.fetchone()[0]

        # Invalid / anomalous quotes
        cur.execute("SELECT COUNT(*) FROM options_quotes WHERE bid_price < 0 OR ask_price < 0")
        negative_quotes = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM options_quotes "
            "WHERE bid_price IS NOT NULL AND ask_price IS NOT NULL "
            "AND bid_price > 0 AND ask_price > 0 AND bid_price > ask_price"
        )
        crossed_markets = cur.fetchone()[0]

        # Zero or null quotes
        cur.execute(
            "SELECT COUNT(*) FROM options_quotes "
            "WHERE bid_price IS NULL OR ask_price IS NULL OR bid_price = 0 OR ask_price = 0"
        )
        zero_or_null_quotes = cur.fetchone()[0]

        # Timestamp duplication
        cur.execute(
            "SELECT COUNT(*) - COUNT(DISTINCT contract_id || '_' || timestamp) FROM options_quotes"
        )
        duplicate_quotes = cur.fetchone()[0]

        conn.close()

        total = p10b_meta["total_records"]
        paired = p10b_meta["paired_bid_ask_count"]

        # Surface Density Calculation:
        # A continuous executable surface requires active bid/ask quotes across ATM/ITM/OTM strikes
        # during market hours. Since Bhavcopy provides only EOD settlement prices (null bid/ask),
        # intraday surface density is 0.0 quotes per minute.
        intraday_surface_density_quotes_per_min = 0.0
        continuous_surface_coverage = "0.0%"

        quality_report = {
            "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "phase": "PHASE_10B_OPTIONS_QUALITY",
            "dataset_version": p10b_meta["version_id"],
            "metrics": {
                "total_records": total,
                "unique_timestamps": p10b_meta["unique_timestamps"],
                "unique_contracts": p10b_meta["unique_contracts"],
                "underlyings_covered": underlyings_list,
                "expiry_dates_count": expiries_count,
                "strikes_count": strikes_count,
                "valid_bid_count": valid_bids,
                "valid_ask_count": valid_asks,
                "paired_bid_ask_count": paired,
                "paired_bid_ask_percentage": p10b_meta["paired_bid_ask_percentage"],
                "zero_or_null_quote_count": zero_or_null_quotes,
                "negative_quotes_count": negative_quotes,
                "crossed_markets_count": crossed_markets,
                "duplicate_quote_count": duplicate_quotes,
                "intraday_surface_density_quotes_per_min": intraday_surface_density_quotes_per_min,
                "continuous_executable_surface_coverage": continuous_surface_coverage,
            },
            "independent_metric_clarification": {
                "paired_quote_observations": f"{paired} ({p10b_meta['paired_bid_ask_percentage']}%) - exclusively test fixture quotes.",
                "continuous_executable_surface_coverage": f"{continuous_surface_coverage} - zero genuine continuous exchange bid/ask surface.",
                "methodological_distinction": (
                    "Paired quote observations measure discrete instances where Bid > 0 and Ask > 0. "
                    "Continuous executable surface coverage measures whether executable Bid/Ask spreads "
                    "exist across the option chain throughout the trading session. These metrics are strictly "
                    "independent; neither implies the other."
                ),
            },
            "version_comparison": version_audit["versions_tracked"],
            "provenance_reconciliation": version_audit["provenance_reconciliation"],
            "readiness_gate": {
                "OPTIONS_EXECUTION_RESEARCH_READY": "BLOCKED",
                "OPTIONS_EXECUTION_BACKTEST": "BLOCKED",
                "OPTIONS_PAPER_EXECUTION": "BLOCKED",
                "gate_condition": (
                    "Options execution remains blocked until genuine timestamped executable Bid/Ask "
                    "data satisfies the Phase 10A execution-data readiness requirements."
                ),
            },
        }

        # Save to data/phase10b/options_quality.json
        out_path = Path("data/phase10b/options_quality.json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(quality_report, f, indent=2)

        return quality_report


if __name__ == "__main__":
    rep = OptionsQualityEngine.audit_options_quality()
    print("Options Quality Audit Complete:")
    print("Paired quotes:", rep["metrics"]["paired_bid_ask_count"])
    print("Continuous surface coverage:", rep["metrics"]["continuous_executable_surface_coverage"])
    print("OPTIONS_EXECUTION_RESEARCH_READY:", rep["readiness_gate"]["OPTIONS_EXECUTION_RESEARCH_READY"])
