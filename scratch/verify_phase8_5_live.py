"""
Phase 8.5 — Real-Market Provider Observation & Paper Execution Verification.

Tests the actual pipeline against genuine live observations from YFinanceMarketProvider.
Strictly truthful:
If the provider returns LTP but no executable Bid/Ask:
-> Logs PAPER EXECUTION BLOCKED / NO_VALID_EXECUTABLE_QUOTE.
Never fabricates Bid/Ask, never substitutes LTP for execution.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root in sys.path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.live_market.service import LiveMarketService
from src.paper_trading.execution_guard import ExecutionGuard
from src.paper_trading.market_hours import get_market_state
from src.paper_trading.service import PaperTradingService


def run_live_verification():
    print("=" * 80)
    print("PHASE 8.5: REAL-MARKET OBSERVATION & PAPER EXECUTION VERIFICATION")
    print("=" * 80)

    # Hard safety check
    guard_status = ExecutionGuard.get_execution_status()
    print(f"Safety Status: LIVE_EXECUTION={guard_status['LIVE_EXECUTION']}, BROKER={guard_status['BROKER_CONNECTIONS']}")
    assert guard_status["ALLOW_LIVE_EXECUTION"] is False

    market_service = LiveMarketService()
    paper_service = PaperTradingService(initial_capital=1_000_000.0)
    paper_service.start_session()

    symbols = ["NIFTY", "BANKNIFTY", "RELIANCE"]
    symbol_display = {"NIFTY": "NIFTY 50", "BANKNIFTY": "BANKNIFTY", "RELIANCE": "RELIANCE"}

    results = []

    for sym in symbols:
        name = symbol_display.get(sym, sym)
        print(f"\n--- Testing paper execution with genuine market observation for {name} ({sym}) ---")
        
        # 1. Submit paper order FIRST (satisfies received_timestamp >= order_submission_timestamp)
        order_res = paper_service.place_order(
            symbol=sym,
            side="BUY",
            quantity=25,
            order_type="MARKET",
        )
        order_id = order_res.get("order_id")
        print(f"Order Submitted: {order_id} (Side: BUY, Qty: 25)")

        # 2. Receive live observation from provider
        quote = market_service.fetch_live_quote(sym)
        received_time = datetime.now(timezone.utc)

        if quote is None:
            print(f"[FAIL] Failed to fetch observation from provider for {name}")
            results.append({
                "provider": "YFinance",
                "symbol": name,
                "provider_timestamp": None,
                "received_timestamp": received_time.isoformat(),
                "data_status": "FETCH_FAILED",
                "bid": None,
                "ask": None,
                "ltp": None,
                "quote_age_seconds": None,
                "market_status": "UNKNOWN",
                "execution_eligibility": "BLOCKED",
                "rejection_reason": "PROVIDER_FETCH_FAILED",
            })
            continue

        provider_ts_str = quote.provider_timestamp
        try:
            provider_ts = datetime.fromisoformat(provider_ts_str) if provider_ts_str else received_time
            if provider_ts.tzinfo is None:
                provider_ts = provider_ts.replace(tzinfo=timezone.utc)
        except Exception:
            provider_ts = received_time

        data_status = quote.status_label.value if hasattr(quote.status_label, "value") else str(quote.status_label)
        ltp = quote.last_price
        bid = getattr(quote, "bid", None)
        ask = getattr(quote, "ask", None)

        quote_age = (received_time - provider_ts).total_seconds() if provider_ts else None
        market_state = get_market_state()

        print(f"Provider:            YFinance")
        print(f"Provider Timestamp:  {provider_ts.isoformat()}")
        print(f"Received Timestamp:  {received_time.isoformat()}")
        print(f"Data Status:         {data_status}")
        print(f"Last Price (LTP):    INR {ltp:,.2f}" if ltp else "None")
        print(f"Bid:                 {bid}")
        print(f"Ask:                 {ask}")
        print(f"Quote Age:           {quote_age:.1f}s" if quote_age is not None else "Unknown")
        print(f"Market State:        {market_state.value}")

        # 3. Process market update in paper execution engine
        update_res = paper_service.process_market_update(
            symbol=sym,
            bid=bid,
            ask=ask,
            ltp=ltp,
            provider_timestamp=provider_ts,
            received_timestamp=received_time,
            data_status=data_status,
            source_provider="YFINANCE",
        )

        fills = update_res.get("fills", [])
        refusals = update_res.get("refusals", [])

        if fills:
            eligibility = "EXECUTED"
            reason = "FILLED"
            print(f"[OK] Execution succeeded: Fill ID {fills[0]['fill_id']} @ INR {fills[0]['fill_price']}")
        else:
            eligibility = "BLOCKED"
            reason = refusals[0]["reason"] if refusals else "NO_MATCHING_CONDITIONS"
            details = refusals[0]["details"] if refusals else ""
            print(f"[BLOCKED] Paper Execution BLOCKED as required: Reason = {reason} ({details})")

        results.append({
            "provider": "YFinance",
            "symbol": name,
            "provider_timestamp": provider_ts.isoformat() if provider_ts else None,
            "received_timestamp": received_time.isoformat(),
            "data_status": data_status,
            "bid": bid,
            "ask": ask,
            "ltp": ltp,
            "quote_age_seconds": round(quote_age, 2) if quote_age is not None else None,
            "market_status": market_state.value,
            "execution_eligibility": eligibility,
            "rejection_reason": reason,
        })

    # Portfolio reconciliation check
    rec = paper_service.reconcile()
    print("\n" + "=" * 80)
    print("ACCOUNTING RECONCILIATION RESULT")
    print(f"Status: {rec['status']}, Is Reconciled: {rec['is_reconciled']}")
    print(f"Cash: INR {rec['ending_cash']:,.2f}, Realized P&L: INR {rec['realized_pnl']:,.2f}")
    print("=" * 80)

    # Save validation report JSON
    out_path = _project_root / "data" / "phase8_5_real_market_validation.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "execution_mode": "PAPER_TRADE",
            "safety_guard": guard_status,
            "reconciliation": rec,
            "observations": results,
        }, f, indent=2)

    print(f"\nReport written to {out_path}")
    return results


if __name__ == "__main__":
    run_live_verification()
