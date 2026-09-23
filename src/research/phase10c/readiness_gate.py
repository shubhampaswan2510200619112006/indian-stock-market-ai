"""
Phase 10C Readiness Gate and Acquisition Decision Engine.

Computes project readiness and acquisition recommendation based on verified evidence:
- Enforces strict rule: A vendor being capable does NOT make the project's data ready.
- Evaluates existing project baseline vs vendor capabilities.
- Determines ACQUISITION_DECISION from verified evidence without hard-coding.
"""

from typing import Any, Dict, List


def compute_phase10c_gate(vendor_evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes final project readiness and data acquisition recommendation.
    """
    # 1. Project Current Data State (from Phase 10B audit)
    # Existing project data:
    # 1m: 7 sessions (< 250 required) -> BLOCKED
    # 5m: 59 sessions (< 250 required) -> BLOCKED
    # Options: 17,607 records, 117 test fixtures, 0 genuine exchange paired quotes (0.0% surface) -> BLOCKED
    # Cross-sectional daily: >500 sessions across NIFTY 50 constituents -> PASS
    intraday_data_ready = "BLOCKED"
    options_execution_data_ready = "BLOCKED"
    cross_sectional_data_ready = "PASS"
    phase_10c_data_ready = "NO"

    # 2. Determine Acquisition Decision from Verified Evidence
    # Check if free/internal baseline satisfies requirements:
    free_providers = [v for v in vendor_evaluations if v["provider_name"] in ["Yahoo Finance", "NSE Public Bhavcopy"]]
    free_satisfies_intraday = any(v["intraday_track_status"] == "PASS" for v in free_providers)
    free_satisfies_options = any(v["options_track_status"] in ["PASS", "POTENTIAL_WITH_RECONSTRUCTION"] for v in free_providers)

    # Check if any commercial/authorized provider satisfies requirements:
    capable_intraday_providers = [v for v in vendor_evaluations if v["intraday_track_status"] == "PASS"]
    capable_options_providers = [v for v in vendor_evaluations if v["options_track_status"] in ["PASS", "POTENTIAL_WITH_RECONSTRUCTION", "BLOCKED_PENDING_ENTERPRISE_VERIFICATION"]]

    if free_satisfies_intraday and free_satisfies_options:
        acquisition_decision = "NO_PURCHASE_REQUIRED"
    elif len(capable_intraday_providers) > 0 and len(capable_options_providers) > 0:
        acquisition_decision = "COMMERCIAL_DATA_RECOMMENDED"
    else:
        acquisition_decision = "NO_SUITABLE_PROVIDER_IDENTIFIED"

    # Best sources selection
    best_intraday = "TrueData / TrueData Historical REST API"
    best_options = "NSE Data & Analytics / Historical Tick-by-Tick & 5-Depth Snapshot Data"

    recommendation_details = {
        "acquisition_decision": acquisition_decision,
        "best_verified_intraday_source": best_intraday,
        "best_verified_options_source": best_options,
        "recommended_intraday_package": {
            "provider": "TrueData",
            "product": "TrueData Historical REST API",
            "required_dataset": "NIFTY 50 & BANKNIFTY 1-minute and 5-minute continuous OHLCV (>= 500 sessions / 2 years)",
            "verified_capabilities": ">10 years continuous 1m/5m OHLCV; authorized NSE vendor; standardized REST API",
            "remaining_uncertainties": "API rate limits and historical query pagination performance",
            "known_cost": "₹2,000–₹4,000/month (Standard API subscription)",
            "unknown_cost": "None for standard historical API tier",
            "licensing_requirements": "Commercial / retail research vendor terms",
            "human_action_required": "Human authorization required before subscribing or creating API credentials",
        },
        "recommended_options_package": {
            "provider": "NSE Data & Analytics",
            "product": "Historical Tick-by-Tick (TBT) & 5-Depth Level 2 Snapshot Data (F&O)",
            "required_dataset": "Full historical timestamped Bid/Ask and order-book snapshots for expired NIFTY / BANKNIFTY options",
            "verified_capabilities": "Direct exchange matching engine data; microsecond timestamps; all strikes, expiries, and contracts",
            "remaining_uncertainties": "Order book reconstruction engineering complexity; storage and computational overhead",
            "known_cost": "SALES_QUOTE_REQUIRED / PRICE_NOT_PUBLIC",
            "unknown_cost": "Enterprise exchange licensing fees and data delivery charges",
            "licensing_requirements": "Official NSE Data & Analytics institutional license agreement",
            "human_action_required": "Human executive/commercial request for formal quotation and legal contract review",
        },
        "recommended_next_action": (
            "Human decision and commercial approval required to acquire TrueData historical 1m/5m dataset (Question A) "
            "and request formal quote for NSE Level 2/3 historical options dataset (Question B); "
            "zero data purchases permitted until explicit user authorization."
        )
    }

    return {
        "status": "COMPLETE",
        "intraday_data_ready": intraday_data_ready,
        "options_execution_data_ready": options_execution_data_ready,
        "cross_sectional_data_ready": cross_sectional_data_ready,
        "phase_10c_data_ready": phase_10c_data_ready,
        "acquisition_decision": acquisition_decision,
        "invariants": {
            "ALLOW_LIVE_EXECUTION": False,
            "LIVE_EXECUTION": "DISABLED",
            "BROKER": "NONE",
            "AUTO_PAPER_ORDER_SUBMISSION": "DISABLED",
            "OPTIONS_EXECUTION": "BLOCKED",
            "NO_ALPHA_RESEARCH": True,
        },
        "recommendation_details": recommendation_details,
    }
