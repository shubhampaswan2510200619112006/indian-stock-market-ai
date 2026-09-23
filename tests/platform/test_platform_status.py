"""
Test Platform Status Reporter and Baseline Verification.
"""

import pytest
from src.platform.status import PlatformStatusReporter


def test_platform_status_dictionary():
    reporter = PlatformStatusReporter()
    status = reporter.get_status_dict()

    assert status["platform_status"] == "COMPLETE"
    assert status["overall_platform_state"] == "RESEARCH_READY_WITH_DATA_LIMITATIONS"

    caps = status["capabilities"]
    assert caps["daily_data"] == "READY"
    assert caps["cross_sectional_equities"] == "READY"
    assert caps["intraday_1m"] == "BLOCKED"
    assert caps["intraday_5m"] == "BLOCKED"
    assert caps["options_historical_bid_ask"] == "BLOCKED"
    assert caps["options_execution"] == "BLOCKED"

    invs = status["safety_invariants"]
    assert invs["ALLOW_LIVE_EXECUTION"] is False
    assert invs["LIVE_EXECUTION"] == "DISABLED"
    assert invs["BROKER"] == "NONE"
    assert invs["AUTO_PAPER_ORDER_SUBMISSION"] == "DISABLED"
    assert invs["NEW_ALPHA_DISCOVERY"] == "DISABLED"
    assert invs["PLATFORM_ENGINEERING"] == "ENABLED"

    base = status["baseline_integrity"]
    assert base["all_baselines_intact"] is True
    assert base["phase_9_7"] == "FROZEN"
    assert base["phase_9_8"] == "FROZEN"
    assert base["phase_9_9"] == "FROZEN_IMMUTABLE"
    assert base["phase_10a"] == "INTACT"
    assert base["phase_10b"] == "INTACT"


def test_platform_status_cli_banner():
    reporter = PlatformStatusReporter()
    banner = reporter.render_cli_banner()
    assert "FINANCIAL RESEARCH PLATFORM" in banner
    assert "DAILY DATA                 READY" in banner
    assert "CROSS-SECTIONAL EQUITIES   READY" in banner
    assert "INTRADAY 1m                BLOCKED" in banner
    assert "INTRADAY 5m                BLOCKED" in banner
    assert "BROKER                     NONE" in banner
    assert "LIVE EXECUTION             DISABLED" in banner
