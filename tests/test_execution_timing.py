"""
Model A Execution Timing & Execution Audit Refusal Tests (Phase 6.5).
"""

from datetime import datetime
import pytest

from src.ml.execution_timing import (
    ExecutionAuditReport,
    ExecutionPriceSource,
    ModelAExecutionTimer,
)


def test_model_a_timestamp_derivation():
    """
    Verifies that Model A derives strict non-overlapping execution timestamps:
    T 15:30 -> T 15:31 -> T+1 09:15
    """
    obs_date = datetime(2026, 8, 14, 15, 30, 0)  # Friday
    t_feat, t_pred, t_order = ModelAExecutionTimer.derive_model_a_timestamps(obs_date)

    assert t_feat == datetime(2026, 8, 14, 15, 30, 0)
    assert t_pred == datetime(2026, 8, 14, 15, 31, 0)
    # Next trading session after Friday is Monday Aug 17
    assert t_order == datetime(2026, 8, 17, 9, 15, 0)


def test_execution_audit_refusal_tracking():
    """
    Verifies that trade execution refusal tracks attempted, successful, refused, and refusal reasons.
    """
    audit = ExecutionAuditReport()

    t_feat = datetime(2026, 8, 14, 15, 30, 0)
    t_pred = datetime(2026, 8, 14, 15, 31, 0)
    t_order = datetime(2026, 8, 17, 9, 15, 0)

    # 1. Successful Execution with genuine historical quote
    rec1 = audit.record_attempt(
        t_feat=t_feat,
        t_pred=t_pred,
        t_order=t_order,
        t_exec=datetime(2026, 8, 17, 9, 15, 30),
        price=150.0,
        source=ExecutionPriceSource.NSE_HISTORICAL_OPTION_QUOTE,
        is_executed=True,
    )
    assert rec1.is_executed
    assert audit.successful_executions == 1

    # 2. Refused Execution due to missing next-session data
    rec2 = audit.record_attempt(
        t_feat=t_feat,
        t_pred=t_pred,
        t_order=t_order,
        t_exec=None,
        price=None,
        source=ExecutionPriceSource.UNAVAILABLE,
        is_executed=False,
        refusal_reason="NEXT_SESSION_EXECUTION_DATA_UNAVAILABLE",
    )
    assert not rec2.is_executed
    assert audit.refused_executions == 1
    assert audit.refusal_reasons["NEXT_SESSION_EXECUTION_DATA_UNAVAILABLE"] == 1

    # 3. Refused Execution due to EOD LTP unsuitable proxy for morning execution
    rec3 = audit.record_attempt(
        t_feat=t_feat,
        t_pred=t_pred,
        t_order=t_order,
        t_exec=datetime(2026, 8, 17, 15, 30, 0),
        price=155.0,
        source=ExecutionPriceSource.EOD_UNSUITABLE_PROXY,
        is_executed=False,
        refusal_reason="EOD_DATA_CANNOT_PROXIMATE_MORNING_EXECUTION",
    )
    assert not rec3.is_executed
    assert audit.refused_executions == 2
    assert audit.attempted_executions == 3
