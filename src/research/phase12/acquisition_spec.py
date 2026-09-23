"""
Phase 12 Data Acquisition Specification Engine.

Formalizes minimum acceptable research criteria and project-defined thresholds:
- INTRADAY_MIN_SESSIONS = 250 (PROJECT_RESEARCH_THRESHOLD)
- PAIR_QUOTE_CONTINUITY_MIN_PCT = 70.0% (PROJECT_RESEARCH_THRESHOLD)
- Contract validation via authoritative exchange specifications and calendar
- Absolute prohibition against data fabrication and unauthorized purchases
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


@dataclass
class IntradayAcquisitionSpecification:
    target_symbols: List[str] = field(default_factory=lambda: ["NIFTY 50", "NIFTY BANK"])
    target_intervals: List[str] = field(default_factory=lambda: ["1m", "5m"])
    minimum_sessions_threshold: int = 250  # PROJECT_RESEARCH_THRESHOLD
    preferred_years_target: str = "3-5 years (~750-1250 sessions)"
    required_columns: List[str] = field(
        default_factory=lambda: ["timestamp", "open", "high", "low", "close", "volume", "symbol"]
    )
    session_start_ist: str = "09:15:00"
    session_end_ist: str = "15:30:00"
    timezone: str = "Asia/Kolkata (+05:30)"
    timestamp_precision: str = "ISO-8601 with timezone or explicit IST minute offset"
    substitutions_permitted: bool = False
    substitution_restriction_note: str = (
        "Substitution of daily or 1-hour bars for 1m/5m intraday data is strictly forbidden."
    )


@dataclass
class OptionsAcquisitionSpecification:
    target_underlyings: List[str] = field(default_factory=lambda: ["NIFTY", "BANKNIFTY"])
    required_columns: List[str] = field(
        default_factory=lambda: [
            "underlying",
            "contract_id",
            "expiry",
            "strike",
            "option_type",
            "timestamp",
            "bid",
            "ask",
            "ltp",
            "volume",
            "open_interest",
        ]
    )
    preferred_additional_columns: List[str] = field(
        default_factory=lambda: ["bid_qty", "ask_qty", "depth_5", "implied_volatility"]
    )
    paired_quote_continuity_threshold_pct: float = 70.0  # PROJECT_RESEARCH_THRESHOLD
    contract_validation_method: str = "EXCHANGE_SPEC_AND_CALENDAR_DRIVEN"
    contract_validation_note: str = (
        "Contract validation must evaluate against authoritative exchange contract specifications "
        "and market holiday calendars; hardcoding Thursdays or Wednesdays as universal rules is forbidden."
    )
    options_quality_hierarchy: Dict[str, str] = field(
        default_factory=lambda: {
            "LEVEL_0": "NO OPTIONS DATA",
            "LEVEL_1": "LTP / SETTLEMENT ONLY",
            "LEVEL_2": "ISOLATED BID/ASK",
            "LEVEL_3": "CONTINUOUS PAIRED BID/ASK (Execution-Ready for Research)",
            "LEVEL_4": "DEPTH / ORDER-BOOK CAPABLE",
        }
    )


@dataclass
class AcquisitionGovernance:
    purchase_authorized: bool = False
    human_decision_required: bool = True
    broker_connection_allowed: bool = False
    live_execution_allowed: bool = False
    paper_automation_allowed: bool = False
    alpha_research_allowed: bool = False
    zero_data_fabrication_rule: str = (
        "Zero synthetic Bid/Ask prices or continuous quote surfaces may be labeled as exchange observations."
    )


class AcquisitionSpecEngine:
    """
    Generates structured specification artifact for Phase 12.
    """

    @classmethod
    def get_full_specification(cls) -> Dict[str, Any]:
        intraday_spec = IntradayAcquisitionSpecification()
        options_spec = OptionsAcquisitionSpecification()
        gov = AcquisitionGovernance()

        return {
            "specification_version": "phase12_v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "governance": asdict(gov),
            "intraday_requirements": asdict(intraday_spec),
            "options_requirements": asdict(options_spec),
            "quality_threshold_classifications": {
                "intraday_minimum_evaluation_threshold": "N >= 250 sessions (PROJECT_RESEARCH_THRESHOLD)",
                "options_quote_continuity_threshold": "paired_quote_coverage >= 70.0% (PROJECT_RESEARCH_THRESHOLD)",
                "contract_weekday_rule": "DYNAMIC_EXCHANGE_SPEC (Not hardcoded day)",
            },
            "acquisition_decision_framework": {
                "decision_states": [
                    "READY_NOW",
                    "ACQUISITION_REQUIRED",
                    "VENDOR_CONFIRMATION_REQUIRED",
                    "NOT_AVAILABLE",
                ],
                "vendor_quote_status_types": [
                    "VERIFIED_QUOTE",
                    "ESTIMATE",
                    "NOT_PUBLISHED",
                    "REQUIRES_VENDOR_QUOTE",
                ],
            },
        }
