"""
Test Automatic Readiness and Execution Gates.
"""

import pytest
from src.platform.gates.readiness_gate import ReadinessGate
from src.platform.gates.execution_gate import ExecutionGate


def test_readiness_gate_daily_index():
    gate = ReadinessGate()
    res = gate.check_prerequisites("daily_index", "CONFIRMATORY", required_sessions=250)
    assert res.permitted is True
    assert res.status == "RESEARCH_PERMITTED"


def test_readiness_gate_cross_sectional_equities():
    gate = ReadinessGate()
    res = gate.check_prerequisites("cross_sectional_equities", "CONFIRMATORY", required_sessions=250)
    assert res.permitted is True
    assert res.status == "RESEARCH_PERMITTED"


def test_readiness_gate_intraday_blocked():
    gate = ReadinessGate()
    res_1m = gate.check_prerequisites("intraday_1m", "CONFIRMATORY", required_sessions=250)
    assert res_1m.permitted is False
    assert res_1m.status == "RESEARCH_BLOCKED"
    assert res_1m.reason == "INSUFFICIENT_VERIFIED_INTRADAY_HISTORY"
    assert "Attach a qualifying" in res_1m.action

    res_5m = gate.check_prerequisites("intraday_5m", "CONFIRMATORY", required_sessions=250)
    assert res_5m.permitted is False
    assert res_5m.status == "RESEARCH_BLOCKED"
    assert "59 sessions" in res_5m.available


def test_readiness_gate_options_execution_blocked():
    gate = ReadinessGate()
    res = gate.check_prerequisites("historical_options_ltp", "EXECUTION")
    assert res.permitted is False
    assert res.status == "RESEARCH_BLOCKED"
    assert "CANNOT_MODEL_SLIPPAGE" in res.reason


def test_execution_gate_live_and_paper_blocked():
    res_paper = ExecutionGate.check_live_or_paper_order("NIFTY", "PAPER")
    assert res_paper.execution_permitted is False
    assert res_paper.status == "EXECUTION_BLOCKED"

    res_live = ExecutionGate.check_live_or_paper_order("RELIANCE", "LIVE")
    assert res_live.execution_permitted is False


def test_execution_gate_options_backtest():
    # L0 and L1 must be blocked
    res_l0 = ExecutionGate.check_backtest_execution("OPTIONS", options_quality_level="LEVEL_0")
    assert res_l0.execution_permitted is False

    res_l2 = ExecutionGate.check_backtest_execution("OPTIONS", options_quality_level="LEVEL_2")
    assert res_l2.execution_permitted is False

    # L3 can be permitted
    res_l3 = ExecutionGate.check_backtest_execution("OPTIONS", options_quality_level="LEVEL_3")
    assert res_l3.execution_permitted is True
