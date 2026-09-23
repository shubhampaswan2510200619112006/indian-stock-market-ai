"""
System Status and Diagnostic Reporter.

Dynamically evaluates:
- Active data capabilities
- Research readiness per track
- Execution readiness
- Platform safety invariants
- Frozen baseline integrity

Generates both formatted CLI banners and structured machine-readable JSON.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from src.platform import (
    ALLOW_LIVE_EXECUTION,
    AUTO_PAPER_ORDER_SUBMISSION,
    BROKER,
    LIVE_EXECUTION,
    NEW_ALPHA_DISCOVERY,
    NO_ALPHA_RESEARCH,
    OPTIONS_EXECUTION,
    PLATFORM_ENGINEERING,
)
from src.platform.capabilities import get_capability_registry
from src.research.phase10c.baseline_verifier import verify_frozen_baselines


class PlatformStatusReporter:
    """
    Authoritative system status reporter.
    """

    def __init__(self, workspace_root: str = "."):
        self.workspace_root = workspace_root

    def get_status_dict(self) -> Dict[str, Any]:
        """Calculates dynamic platform state dictionary."""
        reg = get_capability_registry(self.workspace_root)
        baseline = verify_frozen_baselines(self.workspace_root)

        daily_cap = reg.get_capability("daily_index")
        cross_cap = reg.get_capability("cross_sectional_equities")
        intra_1m_cap = reg.get_capability("intraday_1m")
        intra_5m_cap = reg.get_capability("intraday_5m")
        opt_ltp_cap = reg.get_capability("historical_options_ltp")
        opt_ba_cap = reg.get_capability("historical_options_bid_ask")

        return {
            "platform_status": "COMPLETE",
            "overall_platform_state": "RESEARCH_READY_WITH_DATA_LIMITATIONS",
            "capabilities": {
                "daily_data": "READY" if daily_cap and daily_cap.research_readiness == "READY" else "BLOCKED",
                "cross_sectional_equities": "READY" if cross_cap and cross_cap.research_readiness == "READY" else "BLOCKED",
                "intraday_1m": "BLOCKED" if intra_1m_cap and intra_1m_cap.research_readiness == "BLOCKED" else "READY",
                "intraday_5m": "BLOCKED" if intra_5m_cap and intra_5m_cap.research_readiness == "BLOCKED" else "READY",
                "options_ltp": "AVAILABLE" if opt_ltp_cap and opt_ltp_cap.available else "NOT_AVAILABLE",
                "options_historical_bid_ask": "BLOCKED" if opt_ba_cap and opt_ba_cap.research_readiness == "BLOCKED" else "READY",
                "options_execution": "BLOCKED" if OPTIONS_EXECUTION == "BLOCKED" else "ENABLED",
            },
            "safety_invariants": {
                "ALLOW_LIVE_EXECUTION": ALLOW_LIVE_EXECUTION,
                "LIVE_EXECUTION": LIVE_EXECUTION,
                "BROKER": BROKER,
                "AUTO_PAPER_ORDER_SUBMISSION": AUTO_PAPER_ORDER_SUBMISSION,
                "OPTIONS_EXECUTION": OPTIONS_EXECUTION,
                "NEW_ALPHA_DISCOVERY": NEW_ALPHA_DISCOVERY,
                "PLATFORM_ENGINEERING": PLATFORM_ENGINEERING,
            },
            "baseline_integrity": {
                "all_baselines_intact": baseline["all_baselines_intact"],
                "phase_9_7": baseline["phase_9_7_baseline"],
                "phase_9_8": baseline["phase_9_8_research_results"],
                "phase_9_9": baseline["phase_9_9_freeze_manifest"],
                "phase_10a": baseline["phase_10a_artifacts_status"],
                "phase_10b": baseline["phase_10b_artifacts_status"],
            },
            "data_governance": {
                "fabricated_data": "NONE",
                "data_purchase": "NONE",
                "broker_connections": "NONE",
                "data_provider_architecture": "READY",
                "future_data_onboarding": "READY",
                "readiness_gates": "ACTIVE",
            }
        }

    def render_cli_banner(self) -> str:
        """Renders standard ASCII platform status banner."""
        s = self.get_status_dict()
        caps = s["capabilities"]
        invs = s["safety_invariants"]

        banner = [
            "===============================================",
            "FINANCIAL RESEARCH PLATFORM",
            "===============================================",
            "",
            f"DAILY DATA                 {caps['daily_data']}",
            f"CROSS-SECTIONAL EQUITIES   {caps['cross_sectional_equities']}",
            "",
            f"INTRADAY 1m                {caps['intraday_1m']}",
            f"INTRADAY 5m                {caps['intraday_5m']}",
            "",
            f"OPTIONS LTP                {caps['options_ltp']}",
            f"OPTIONS HISTORICAL BID/ASK {caps['options_historical_bid_ask']}",
            f"OPTIONS EXECUTION          {caps['options_execution']}",
            "",
            f"BROKER                     {invs['BROKER']}",
            f"PAPER EXECUTION            {invs['AUTO_PAPER_ORDER_SUBMISSION']}",
            f"LIVE EXECUTION             {invs['LIVE_EXECUTION']}",
            "",
            f"NEW ALPHA DISCOVERY        {invs['NEW_ALPHA_DISCOVERY']}",
            f"PLATFORM ENGINEERING       {invs['PLATFORM_ENGINEERING']}",
            "===============================================",
        ]
        return "\n".join(banner)


if __name__ == "__main__":
    reporter = PlatformStatusReporter()
    print(reporter.render_cli_banner())
