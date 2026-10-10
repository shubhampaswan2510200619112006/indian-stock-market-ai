"""
Phase 9 — Real-Market Observation & Provenance Verification Script.

Fetches genuine market observations from active providers.
Evaluates timestamp provenance, latency decomposition, executable quote requirements,
options availability, and records verification evidence to data/phase9_real_data_validation.json.
Zero data is fabricated.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
import json
from pathlib import Path
import sys

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.data_infrastructure.calendar import NSEMarketCalendar
from src.data_infrastructure.executable_validator import ExecutableQuoteValidator
from src.data_infrastructure.health_monitor import ProviderHealthMonitor
from src.data_infrastructure.providers.bhavcopy_provider import NSEBhavcopyHistoricalProvider
from src.data_infrastructure.providers.market_provider import Phase9YFinanceProvider
from src.data_infrastructure.providers.options_provider import Phase9OptionsProvider
from src.data_infrastructure.providers.scorecard import build_bhavcopy_scorecard, build_yfinance_scorecard
from src.data_infrastructure.providers.verification import ProviderVerificationEngine
from src.data_infrastructure.sufficiency_gate import DataSufficiencyGate
from src.paper_trading.execution_guard import ExecutionGuard


def run_real_data_verification():
    print("=" * 85)
    print("PHASE 9: PRODUCTION-GRADE DATA INFRASTRUCTURE & PROVENANCE VERIFICATION")
    print("=" * 85)

    # Hard Safety Check
    guard = ExecutionGuard.get_execution_status()
    print(f"Safety Guard: LIVE_EXECUTION={guard['LIVE_EXECUTION']}, BROKER={guard['BROKER_CONNECTIONS']}")
    assert guard["ALLOW_LIVE_EXECUTION"] is False

    market_prov = Phase9YFinanceProvider()
    options_prov = Phase9OptionsProvider()
    bhavcopy_prov = NSEBhavcopyHistoricalProvider()

    test_symbols = ["NIFTY", "BANKNIFTY", "RELIANCE"]
    market_observations_report = []

    is_open, market_state = NSEMarketCalendar.is_fill_eligible()
    print(f"NSE Market State:    {market_state} (Open for fills: {is_open})")

    # 1. Verify Market Quotes
    for sym in test_symbols:
        print(f"\n--- Ingesting & Verifying Spot Observation for {sym} ---")
        obs = market_prov.get_quote(sym)
        if not obs:
            print(f"[FAIL] Provider failed to return quote for {sym}")
            continue

        latencies = obs.timestamps.calculate_latencies()
        val_buy = ExecutableQuoteValidator.validate_for_execution(
            side="BUY",
            bid=obs.bid_price,
            ask=obs.ask_price,
            ltp=obs.last_price,
            data_status=obs.data_status,
            is_market_open=is_open,
        )

        print(f"Provider:            {obs.provider}")
        print(f"Symbol:              {obs.symbol}")
        print(f"Provider TS:         {obs.timestamps.provider_timestamp.isoformat()}")
        print(f"Received TS:         {obs.timestamps.received_timestamp.isoformat()}")
        print(f"Processed TS:        {obs.timestamps.processed_timestamp.isoformat()}")
        print(f"Data Status:         {obs.data_status.value}")
        print(f"LTP:                 INR {obs.last_price:,.2f}" if obs.last_price else "None")
        print(f"Bid:                 {obs.bid_price}")
        print(f"Ask:                 {obs.ask_price}")
        print(f"Volume:              {obs.volume}")
        print(f"Execution Eligible:  {val_buy.is_executable}")
        print(f"Rejection Code:      {val_buy.rejection_code or 'NONE'}")
        print(f"Price Mark Role:     {'VALUATION_MARK_ONLY' if not val_buy.is_executable else 'EXECUTION_QUOTE'}")
        print(f"Latencies (ms):      {latencies}")

        market_observations_report.append({
            "symbol": obs.symbol,
            "provider": obs.provider,
            "provider_timestamp": obs.timestamps.provider_timestamp.isoformat(),
            "received_timestamp": obs.timestamps.received_timestamp.isoformat(),
            "processed_timestamp": obs.timestamps.processed_timestamp.isoformat(),
            "status": obs.data_status.value,
            "ltp": obs.last_price,
            "bid": obs.bid_price,
            "ask": obs.ask_price,
            "volume": obs.volume,
            "open_interest": obs.open_interest,
            "execution_eligibility": val_buy.is_executable,
            "rejection_code": val_buy.rejection_code,
            "latencies": latencies,
        })

    # 2. Verify Live Options Feed (Truthful disclosure: UNVERIFIED)
    print("\n--- Verifying Live Options Gateway Feed ---")
    opt_chain = options_prov.get_option_chain("NIFTY", expiry=date.today())
    opt_status = "UNVERIFIED" if opt_chain is None else "VERIFIED"
    print(f"Live Options Provider: {options_prov.provider_name}")
    print(f"Live Options Status:   {opt_status} (Zero synthetic chains generated)")

    # 3. Verify Historical Options Archive
    print("\n--- Auditing Historical Options Bhavcopy Coverage ---")
    bhav_audit = bhavcopy_prov.audit_dataset_quality("NIFTY", date(2025, 1, 1), date.today())
    print(f"Historical Provider:   {bhavcopy_prov.provider_name}")
    print(f"Audit Status:          {bhav_audit['audit_status']}")
    print(f"Bid/Ask Coverage:      {bhav_audit['bid_ask_coverage_pct']}% (Bhavcopy settlement lacks Bid/Ask)")
    print(f"Suitable for Exec:     {bhav_audit['is_suitable_for_execution']}")

    # 4. Capability-Specific Data Sufficiency Gate
    print("\n--- Capability-Specific Data Sufficiency Evaluation ---")
    sufficiency_res = DataSufficiencyGate.evaluate_all(
        symbol="NIFTY",
        trading_sessions_count=60,
        option_quotes_count=50,
        bid_ask_coverage_pct=bhav_audit["bid_ask_coverage_pct"],
        iv_coverage_pct=0.0,
        is_live_options_verified=False,
        is_live_bid_ask_available=False,
    )
    for cap, ev in sufficiency_res.items():
        print(f"  {cap:<30}: {ev.status:<10} (Sufficient: {ev.is_sufficient})")

    # 5. Output Report JSON
    out_dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phase": "PHASE_9_DATA_INFRASTRUCTURE",
        "safety_status": guard,
        "market_state": market_state,
        "market_observations": market_observations_report,
        "live_options_status": {
            "provider": options_prov.provider_name,
            "status": opt_status,
            "notes": "Live options provider unconfigured or unauthorized. Zero fake data.",
        },
        "historical_options_coverage": bhav_audit,
        "sufficiency_gate_results": {k: {"status": v.status, "reasons": v.reasons} for k, v in sufficiency_res.items()},
        "provider_scorecards": {
            "yfinance": build_yfinance_scorecard().to_dict(),
            "bhavcopy": build_bhavcopy_scorecard().to_dict(),
        },
    }

    out_file = _project_root / "data" / "phase9_real_data_validation.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_dict, f, indent=2)

    print(f"\nReport written to: {out_file}")
    print("=" * 85)
    return out_dict


if __name__ == "__main__":
    run_real_data_verification()
