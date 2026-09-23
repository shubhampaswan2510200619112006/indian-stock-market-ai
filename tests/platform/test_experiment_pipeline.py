"""
Test Disciplined Experiment Pipeline.
"""

import pytest
import pandas as pd
import numpy as np
from src.platform.pipeline.experiment_pipeline import (
    ExperimentPipeline,
    ExperimentDefinition,
)


def test_experiment_blocked_at_data_gate():
    pipeline = ExperimentPipeline()
    exp_def = ExperimentDefinition(
        hypothesis_id="EXP-INTRADAY-001",
        name="Test Intraday ORB",
        required_data_capability="intraday_5m",
        minimum_sessions_required=250,
        research_type="CONFIRMATORY",
    )

    res = pipeline.run_experiment(exp_def)
    assert res.status == "BLOCKED"
    assert res.gate_result.permitted is False
    assert res.gate_result.reason == "INSUFFICIENT_VERIFIED_INTRADAY_HISTORY"


def test_experiment_runs_on_ready_cross_sectional_data():
    pipeline = ExperimentPipeline()
    exp_def = ExperimentDefinition(
        hypothesis_id="EXP-CS-001",
        name="Test Cross-Sectional Factor Dispersion",
        required_data_capability="cross_sectional_equities",
        minimum_sessions_required=250,
        research_type="CONFIRMATORY",
        execution_model="ESTIMATED_SLIPPAGE",
    )

    mock_data = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=350, freq="B"),
        "close": np.linspace(100.0, 150.0, 350),
        "volume": [100000] * 350,
    })

    res = pipeline.run_experiment(exp_def, input_data=mock_data)
    assert res.gate_result.permitted is True
    assert res.status in ["COMPLETED", "REJECTED"]
    assert res.sample_size > 0
    assert "friction_bps" in res.details
