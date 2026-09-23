"""
Tests for Phase 9 Capability-Specific Data Sufficiency Gate.
"""

import pytest

from src.data_infrastructure.sufficiency_gate import DataSufficiencyGate


def test_feature_generation_sufficiency():
    # 20 sessions -> PASS
    eval_pass = DataSufficiencyGate.check_feature_generation(sessions_count=20)
    assert eval_pass.status == "PASS"
    assert eval_pass.is_sufficient is True

    # 8 sessions -> WARNING
    eval_warn = DataSufficiencyGate.check_feature_generation(sessions_count=8)
    assert eval_warn.status == "WARNING"
    assert eval_warn.is_sufficient is True

    # 3 sessions -> FAIL
    eval_fail = DataSufficiencyGate.check_feature_generation(sessions_count=3)
    assert eval_fail.status == "FAIL"
    assert eval_fail.is_sufficient is False


def test_equity_backtest_sufficiency():
    # 30 sessions -> PASS
    assert DataSufficiencyGate.check_equity_backtest(30).status == "PASS"

    # 5 sessions -> FAIL
    eval_fail = DataSufficiencyGate.check_equity_backtest(5)
    assert eval_fail.status == "FAIL"
    assert eval_fail.is_sufficient is False


def test_options_execution_backtest_requires_bid_ask():
    # 50 quotes, 0% Bid/Ask -> FAIL for execution backtest
    eval_zero_ba = DataSufficiencyGate.check_options_execution_backtest(
        option_quotes_count=50,
        bid_ask_coverage_pct=0.0,
    )
    assert eval_zero_ba.status == "FAIL"
    assert eval_zero_ba.is_sufficient is False
    assert any("Bid/Ask coverage" in r for r in eval_zero_ba.reasons)

    # 50 quotes, 90% Bid/Ask -> PASS
    eval_pass = DataSufficiencyGate.check_options_execution_backtest(
        option_quotes_count=50,
        bid_ask_coverage_pct=90.0,
    )
    assert eval_pass.status == "PASS"
    assert eval_pass.is_sufficient is True


def test_options_paper_execution_is_blocked_when_unverified():
    eval_block = DataSufficiencyGate.check_options_paper_execution(is_live_options_verified=False)
    assert eval_block.status == "BLOCKED"
    assert eval_block.is_sufficient is False
    assert "OPTIONS PAPER TRADING: BLOCKED" in eval_block.reasons[0]


def test_ml_training_sufficiency():
    # 70 sessions -> PASS
    assert DataSufficiencyGate.check_ml_training(70).status == "PASS"

    # 15 sessions -> FAIL
    eval_fail = DataSufficiencyGate.check_ml_training(15)
    assert eval_fail.status == "FAIL"
    assert eval_fail.is_sufficient is False
