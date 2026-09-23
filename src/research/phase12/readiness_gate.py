"""
Phase 12 Readiness Gate Engine.

Enforces independent readiness evaluations:
- INTRADAY_1M_READY
- INTRADAY_5M_READY
- OPTIONS_LTP_READY
- OPTIONS_BID_ASK_READY
- OPTIONS_EXECUTION_READY

Maintains strict governance:
- PURCHASE_AUTHORIZED = FALSE
- HUMAN_DECISION_REQUIRED = TRUE
- ZERO automatic unlock of future research phases
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from src.research.phase12.baseline_verifier import verify_frozen_baselines


@dataclass
class GateEvaluationResult:
    phase_12_status: str  # COMPLETE, BLOCKED
    intraday_1m_ready: str  # PASS, BLOCKED
    intraday_5m_ready: str  # PASS, BLOCKED
    options_ltp_ready: str  # PASS, BLOCKED
    options_bid_ask_ready: str  # PASS, BLOCKED
    options_execution_ready: str  # PASS, BLOCKED
    data_provenance: str  # PASS, BLOCKED
    data_license_status: str  # PASS, BLOCKED, REQUIRES_AUTHORIZATION
    commercial_acquisition_required: bool
    purchase_authorized: bool
    human_decision_required: bool
    broker: str
    live_execution: str
    auto_paper_order_submission: str
    new_alpha_research: str
    frozen_baselines: str
    reasons_for_blocking: List[str] = field(default_factory=list)
    acquisition_decision_package: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Phase12ReadinessGate:
    """
    Evaluates Phase 12 data acquisition and readiness states.
    """

    @classmethod
    def evaluate(cls, workspace_root: str = ".") -> GateEvaluationResult:
        baseline_check = verify_frozen_baselines(workspace_root)
        baselines_intact = baseline_check.get("all_baselines_intact", False)

        reasons = []

        if not baselines_intact:
            reasons.append("Frozen baseline integrity check failed")

        # Evaluate Intraday 1m Readiness
        intraday_1m_sessions = 7  # Empirically observed in Phase 10A/10B for public 1m endpoint
        if intraday_1m_sessions < 250:
            intraday_1m_ready = "BLOCKED"
            reasons.append(
                f"INTRADAY_1M_READY is BLOCKED: Available public data ({intraday_1m_sessions} sessions) fails PROJECT_RESEARCH_THRESHOLD of 250 sessions."
            )
        else:
            intraday_1m_ready = "PASS"

        # Evaluate Intraday 5m Readiness
        intraday_5m_sessions = 43  # Empirically observed in Phase 10A/10B for public 5m endpoint
        if intraday_5m_sessions < 250:
            intraday_5m_ready = "BLOCKED"
            reasons.append(
                f"INTRADAY_5M_READY is BLOCKED: Available public data ({intraday_5m_sessions} sessions) fails PROJECT_RESEARCH_THRESHOLD of 250 sessions."
            )
        else:
            intraday_5m_ready = "PASS"

        # Evaluate Options Readiness
        # Baseline options dataset: data/indian_options.db (19,643 records, 99.34% Bhavcopy settlement/LTP)
        options_db_path = os.path.join(workspace_root, "data", "indian_options.db")
        options_ltp_ready = "PASS" if os.path.exists(options_db_path) else "BLOCKED"

        # Bid/Ask and Execution Readiness:
        # Phase 10A and Phase 10B proved that the 15,106 records are settlement/LTP records without continuous paired Bid/Ask
        options_bid_ask_ready = "BLOCKED"
        reasons.append("OPTIONS_BID_ASK_READY is BLOCKED: Historical options dataset lacks paired Bid/Ask quotes.")

        options_execution_ready = "BLOCKED"
        reasons.append("OPTIONS_EXECUTION_READY is BLOCKED: Level 1 LTP only; Level 3/4 continuous surface missing.")

        # Commercial Acquisition Status
        commercial_acquisition_required = True
        purchase_authorized = False
        human_decision_required = True

        decision_package = {
            "recommended_primary_source": "NSE Data & Analytics Ltd (Official Exchange Archives)",
            "recommended_secondary_source": "TrueData (Authorized Vendor API & Historical Tick Archives)",
            "target_datasets": [
                "NIFTY 50 & NIFTY BANK 1-Minute and 5-Minute Intraday (Multi-Year, >= 250 sessions)",
                "NIFTY & BANKNIFTY Options Historical Intraday Level 2 / 5-Depth Quote Archives",
            ],
            "estimated_commercial_cost": "REQUIRES_VENDOR_QUOTE (NSE DotEx) / ESTIMATE INR 25k-60k/yr (TrueData)",
            "licensing_considerations": "Commercial proprietary quantitative research license required; zero external redistribution",
            "why_existing_free_data_is_insufficient": (
                "1. Public endpoints (Yahoo Finance) exhibit hard retention limitations (7 days for 1m, 60 days for 5m).\n"
                "2. Retail broker APIs prune expired options contracts immediately upon expiry and provide only OHLCV bars, never historical Bid/Ask quotes."
            ),
            "validation_criteria_upon_acquisition": (
                "All incoming datasets must pass the formal 11-stage DataOnboardingValidator with >= 250 sessions (intraday) "
                "and >= 70% paired quote coverage (options Level 3)."
            ),
        }

        gate_status = "COMPLETE" if baselines_intact else "BLOCKED"

        return GateEvaluationResult(
            phase_12_status=gate_status,
            intraday_1m_ready=intraday_1m_ready,
            intraday_5m_ready=intraday_5m_ready,
            options_ltp_ready=options_ltp_ready,
            options_bid_ask_ready=options_bid_ask_ready,
            options_execution_ready=options_execution_ready,
            data_provenance="PASS",
            data_license_status="REQUIRES_AUTHORIZATION",
            commercial_acquisition_required=commercial_acquisition_required,
            purchase_authorized=purchase_authorized,
            human_decision_required=human_decision_required,
            broker="NONE",
            live_execution="DISABLED",
            auto_paper_order_submission="DISABLED",
            new_alpha_research="DISABLED",
            frozen_baselines="INTACT" if baselines_intact else "FAILED",
            reasons_for_blocking=reasons,
            acquisition_decision_package=decision_package,
        )


if __name__ == "__main__":
    res = Phase12ReadinessGate.evaluate()
    print(json.dumps(res.to_dict(), indent=2))
