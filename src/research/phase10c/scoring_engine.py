"""
Phase 10C Suitability Scoring Engine.

Implements the exact 100-point suitability framework from Phase 10C Section 15:
- Intraday historical depth: 20
- Intraday granularity: 10
- Options Bid/Ask quality: 25
- Options historical depth: 15
- Timestamp/execution quality: 10
- Data completeness: 5
- Provenance/documentation: 5
- Access practicality: 5
- Cost efficiency: 5
TOTAL: 100 points.

Also enforces Section 16 Critical-Fail Overrides:
- Missing critical intraday requirement -> INTRADAY_DATA_TRACK = BLOCKED
- Missing critical options Bid/Ask requirement -> OPTIONS_EXECUTION_TRACK = BLOCKED
"""

import os
import sys
from typing import Any, Dict, List

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from src.research.phase10c.options_level_evaluator import evaluate_options_level


def score_vendor(vendor_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes dimensional and overall suitability score for a single vendor.
    """
    name = vendor_record.get("provider_name", "")
    opt_eval = evaluate_options_level(vendor_record)
    
    breakdown = {}
    critical_flags = []

    # 1. Intraday historical depth (20 pts)
    if name == "NSE Data & Analytics":
        score_intra_depth = 20
        intra_depth_notes = ">10 years historical data available from exchange archives."
    elif name in ["TrueData", "GlobalDataFeeds / GDFL"]:
        score_intra_depth = 20
        intra_depth_notes = ">5-10 years continuous 1m/5m history."
    elif name in ["Zerodha Kite Connect", "Upstox", "Angel One SmartAPI"]:
        score_intra_depth = 14
        intra_depth_notes = "1-2 years 1m/5m available via chunked API requests."
    elif name == "FYERS":
        score_intra_depth = 10
        intra_depth_notes = "~100 days 1m, 1-2 years 5m."
    elif name == "Yahoo Finance":
        score_intra_depth = 2
        intra_depth_notes = "7 days (1m), 59 days (5m); strictly below 250 sessions requirement."
        critical_flags.append("INTRADAY_BELOW_250_SESSIONS")
    elif name == "NSE Public Bhavcopy":
        score_intra_depth = 0
        intra_depth_notes = "EOD settlement data only; zero intraday bars."
        critical_flags.append("NO_INTRADAY_DATA")
    else:
        score_intra_depth = 0
        intra_depth_notes = "Unknown intraday depth."
    breakdown["intraday_historical_depth"] = score_intra_depth

    # 2. Intraday granularity (10 pts)
    if name in ["NSE Data & Analytics", "TrueData", "GlobalDataFeeds / GDFL", "Zerodha Kite Connect", "Upstox", "Angel One SmartAPI", "FYERS"]:
        score_intra_gran = 10
        intra_gran_notes = "Both 1-minute and 5-minute granularities available."
    elif name == "Yahoo Finance":
        score_intra_gran = 4
        intra_gran_notes = "1m and 5m endpoints exist but have very short retention windows."
    elif name == "NSE Public Bhavcopy":
        score_intra_gran = 0
        intra_gran_notes = "Daily resolution only."
    else:
        score_intra_gran = 0
        intra_gran_notes = "Unknown granularity."
    breakdown["intraday_granularity"] = score_intra_gran

    # 3. Options Bid/Ask quality (25 pts)
    if name == "NSE Data & Analytics":
        score_opt_quality = 22
        opt_quality_notes = "Level 2 (5-depth) snapshots and Level 3 TBT logs contain genuine Bid/Ask; requires reconstruction pipeline."
    elif name in ["TrueData", "GlobalDataFeeds / GDFL"]:
        score_opt_quality = 8
        opt_quality_notes = "Standard API serves OHLCV/OI (Level 1); tick Bid/Ask archives unverified and require enterprise contract."
        critical_flags.append("OPTIONS_BID_ASK_NOT_VERIFIED_OUT_OF_BOX")
    elif name in ["Zerodha Kite Connect", "Upstox", "Angel One SmartAPI", "FYERS"]:
        score_opt_quality = 0
        opt_quality_notes = "Documented historical endpoint provides strictly LTP OHLCV; zero Bid/Ask fields."
        critical_flags.append("OPTIONS_BID_ASK_UNAVAILABLE")
    elif name in ["Yahoo Finance", "NSE Public Bhavcopy"]:
        score_opt_quality = 0
        opt_quality_notes = "Zero historical options Bid/Ask."
        critical_flags.append("OPTIONS_BID_ASK_UNAVAILABLE")
    else:
        score_opt_quality = 0
        opt_quality_notes = "Unknown options Bid/Ask."
    breakdown["options_bid_ask_quality"] = score_opt_quality

    # 4. Options historical depth (15 pts)
    if name in ["NSE Data & Analytics", "NSE Public Bhavcopy"]:
        score_opt_depth = 15
        opt_depth_notes = ">10 years expired options contract history."
    elif name in ["TrueData", "GlobalDataFeeds / GDFL"]:
        score_opt_depth = 12
        opt_depth_notes = "Multi-year expired options contracts in OHLCV format."
    elif name in ["Zerodha Kite Connect", "Upstox", "Angel One SmartAPI", "FYERS"]:
        score_opt_depth = 0
        opt_depth_notes = "Expired options contracts purged upon expiry."
        critical_flags.append("NO_EXPIRED_OPTIONS_HISTORY")
    elif name == "Yahoo Finance":
        score_opt_depth = 0
        opt_depth_notes = "No historical expired options data."
        critical_flags.append("NO_EXPIRED_OPTIONS_HISTORY")
    else:
        score_opt_depth = 0
        opt_depth_notes = "Unknown options depth."
    breakdown["options_historical_depth"] = score_opt_depth

    # 5. Timestamp / execution quality (10 pts)
    if name == "NSE Data & Analytics":
        score_timestamp = 10
        timestamp_notes = "Exchange matching engine microsecond/nanosecond timestamps."
    elif name in ["TrueData", "GlobalDataFeeds / GDFL"]:
        score_timestamp = 8
        timestamp_notes = "Feed engine millisecond/second timestamps."
    elif name in ["Zerodha Kite Connect", "Upstox", "Angel One SmartAPI", "FYERS", "Yahoo Finance"]:
        score_timestamp = 6
        timestamp_notes = "Bar minute timestamps."
    elif name == "NSE Public Bhavcopy":
        score_timestamp = 3
        timestamp_notes = "Daily date timestamps."
    else:
        score_timestamp = 0
        timestamp_notes = "Unknown timestamp quality."
    breakdown["timestamp_execution_quality"] = score_timestamp

    # 6. Data completeness (5 pts)
    if name == "NSE Data & Analytics":
        score_completeness = 5
        completeness_notes = "Complete exchange universe (cash, indices, equity F&O, currency F&O)."
    elif name in ["TrueData", "GlobalDataFeeds / GDFL"]:
        score_completeness = 5
        completeness_notes = "Broad coverage of indices, equities, and derivatives."
    elif name in ["Zerodha Kite Connect", "Upstox", "Angel One SmartAPI", "FYERS"]:
        score_completeness = 3
        completeness_notes = "Active symbols complete; expired derivatives purged."
    elif name == "NSE Public Bhavcopy":
        score_completeness = 4
        completeness_notes = "EOD universe complete for exchange traded contracts."
    elif name == "Yahoo Finance":
        score_completeness = 2
        completeness_notes = "Select indices and equities only; derivative chains partial."
    else:
        score_completeness = 0
        completeness_notes = "Unknown completeness."
    breakdown["data_completeness"] = score_completeness

    # 7. Provenance / documentation (5 pts)
    if name in ["NSE Data & Analytics", "NSE Public Bhavcopy"]:
        score_provenance = 5
        provenance_notes = "Direct primary exchange documentation and technical specifications."
    elif name in ["TrueData", "GlobalDataFeeds / GDFL"]:
        score_provenance = 5
        provenance_notes = "Authorized NSE data vendor with published API specifications."
    elif name in ["Zerodha Kite Connect", "Upstox", "Angel One SmartAPI", "FYERS"]:
        score_provenance = 4
        provenance_notes = "Official broker API documentation."
    elif name == "Yahoo Finance":
        score_provenance = 2
        provenance_notes = "Community / unofficial endpoint wrapping public chart API."
    else:
        score_provenance = 0
        provenance_notes = "Unknown provenance."
    breakdown["provenance_documentation"] = score_provenance

    # 8. Access practicality (5 pts)
    if name in ["TrueData", "Zerodha Kite Connect", "Upstox", "Angel One SmartAPI", "FYERS"]:
        score_access = 5
        access_notes = "Turnkey REST APIs and Python SDKs."
    elif name == "Yahoo Finance":
        score_access = 4
        access_notes = "Free public HTTP library (yfinance)."
    elif name == "NSE Public Bhavcopy":
        score_access = 4
        access_notes = "Direct web download / automated CSV scraping."
    elif name in ["GlobalDataFeeds / GDFL"]:
        score_access = 4
        access_notes = "Desktop COM/DLL and REST API."
    elif name == "NSE Data & Analytics":
        score_access = 2
        access_notes = "Heavy enterprise delivery: S3/SFTP or physical media; requires institutional onboarding."
    else:
        score_access = 0
        access_notes = "Unknown access practicality."
    breakdown["access_practicality"] = score_access

    # 9. Cost efficiency (5 pts)
    if name in ["Yahoo Finance", "NSE Public Bhavcopy"]:
        score_cost = 5
        cost_notes = "Free."
    elif name in ["Upstox", "Angel One SmartAPI", "FYERS"]:
        score_cost = 5
        cost_notes = "Free with active trading account."
    elif name in ["Zerodha Kite Connect", "TrueData", "GlobalDataFeeds / GDFL"]:
        score_cost = 3
        cost_notes = "Moderate retail subscription (₹2,000–₹4,000/month)."
    elif name == "NSE Data & Analytics":
        score_cost = 1
        cost_notes = "Enterprise institutional pricing (sales quote required, high financial commitment)."
    else:
        score_cost = 0
        cost_notes = "Unknown cost."
    breakdown["cost_efficiency"] = score_cost

    total_score = sum(breakdown.values())

    # Critical-Fail Overrides (Section 16)
    # 1. Intraday Track Check
    # Requirement: NIFTY/BANKNIFTY 1m and 5m history >= 250 trading sessions
    if name in ["NSE Data & Analytics", "TrueData", "GlobalDataFeeds / GDFL", "Zerodha Kite Connect", "Upstox", "Angel One SmartAPI", "FYERS"]:
        intraday_track_status = "PASS"
    else:
        intraday_track_status = "BLOCKED"

    # 2. Options Execution Track Check
    # Requirement: Genuine historical timestamped Bid/Ask (Level 2/3)
    if name == "NSE Data & Analytics":
        options_track_status = "POTENTIAL_WITH_RECONSTRUCTION"
    elif name in ["TrueData", "GlobalDataFeeds / GDFL"]:
        options_track_status = "BLOCKED_PENDING_ENTERPRISE_VERIFICATION"
    else:
        options_track_status = "BLOCKED"

    return {
        "provider_name": name,
        "product_name": vendor_record.get("product_name", ""),
        "total_score": total_score,
        "max_score": 100,
        "score_breakdown": breakdown,
        "critical_flags": critical_flags,
        "intraday_track_status": intraday_track_status,
        "options_track_status": options_track_status,
        "options_evaluation": opt_eval,
    }


def score_all_vendors(vendor_catalog: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Scores all vendors in the catalog."""
    return [score_vendor(v) for v in vendor_catalog]
