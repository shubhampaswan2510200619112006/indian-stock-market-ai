"""
Test Options Quality Levels and Critical Rules for Phase 10C.
"""

import pytest
from src.research.phase10c.vendor_catalog import get_vendor_catalog
from src.research.phase10c.options_level_evaluator import evaluate_options_level


def test_broker_critical_rule_options_insufficient():
    """
    Test Section 10: Broker endpoints that provide only OHLCV/OI must receive
    OPTIONS_EXECUTION_DATA = INSUFFICIENT and not Level 3/4.
    """
    catalog = {v["provider_name"]: v for v in get_vendor_catalog()}
    for broker_name in ["Zerodha Kite Connect", "Upstox", "Angel One SmartAPI", "FYERS"]:
        broker_record = catalog[broker_name]
        eval_res = evaluate_options_level(broker_record)
        assert eval_res["options_execution_data_status"] == "INSUFFICIENT"
        assert eval_res["options_execution_level"] == "LEVEL_0"
        assert eval_res["level_number"] == 0
        assert "LTP-derived OHLCV" in eval_res["notes"]


def test_nse_critical_rule():
    """
    Test Section 11: NSE historical data must not be marked ready-made Level 3/4
    without an explicit order reconstruction pipeline.
    """
    catalog = {v["provider_name"]: v for v in get_vendor_catalog()}
    nse_record = catalog["NSE Data & Analytics"]
    eval_res = evaluate_options_level(nse_record)
    assert eval_res["level_number"] == 2
    assert "RECONSTRUCTION_PIPELINE_REQUIRED" in eval_res["continuous_surface_status"]
    assert eval_res["options_execution_data_status"] == "ENTERPRISE_ACQUISITION_CANDIDATE"


def test_baselines_options_insufficient():
    """Verify Yahoo Finance and NSE Bhavcopy fail options execution quality."""
    catalog = {v["provider_name"]: v for v in get_vendor_catalog()}
    yfin_eval = evaluate_options_level(catalog["Yahoo Finance"])
    bhav_eval = evaluate_options_level(catalog["NSE Public Bhavcopy"])

    assert yfin_eval["options_execution_data_status"] == "INSUFFICIENT"
    assert bhav_eval["options_execution_data_status"] == "INSUFFICIENT"
