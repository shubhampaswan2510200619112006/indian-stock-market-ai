# Phase 8: Paper Trading & Simulated Live Execution Engine

## 1. Executive Summary & Safety Guarantees

Phase 8 provides a realistic, simulated paper trading execution framework that mirrors production trading workflows without connecting to any broker or placing any real orders.

```
+-------------------------------------------------------------+
|                     HARD SAFETY RULES                       |
+-------------------------------------------------------------+
| LIVE EXECUTION:     DISABLED (Immutable constant: False)    |
| BROKER CONNECTIONS: NONE                                    |
| PAPER EXECUTION:    ENABLED (Simulated execution only)      |
| ORDER TAGGING:      All orders tagged "PAPER_TRADE"         |
+-------------------------------------------------------------+
```

### Safety Guard
The `ExecutionGuard` class unconditionally rejects any attempt to place live orders or connect to a real exchange/broker with `LiveExecutionDisabledError`. It is impossible to bypass this guard without modifying immutable class variables.

---

## 2. Core Architecture

The paper trading system follows a strict pipeline:

$$\text{Decision} \longrightarrow \text{Risk Check} \longrightarrow \text{Order Entry} \longrightarrow \text{Market/Fill Model} \longrightarrow \text{Position Tracking} \longrightarrow \text{Journal} \longrightarrow \text{Reconciliation}$$

### Components

1. **`ExecutionGuard`** (`src/paper_trading/execution_guard.py`):
   - Enforces simulation boundaries.
   - Throws `LiveExecutionDisabledError` if `is_live` is asserted.

2. **`MarketHoursManager`** (`src/paper_trading/market_hours.py`):
   - Validates trading session state against NSE calendar (09:15 to 15:30 IST, Monday–Friday, excluding holidays).
   - Rejects or queues market orders during market-closed periods.

3. **`SimulatedFillEngine`** (`src/paper_trading/fill_engine.py`):
   - Realistic Indian market slippage model based on underlying ADV and order size.
   - Genuine latency simulation (30ms - 250ms simulated fill delays).
   - Partial fill logic when order size exceeds liquidity thresholds.
   - Exchange fee calculations for NSE (STT, Transaction Charges, SEBI turnover, Stamp Duty, GST).
   - Strict adherence to verifiable quotes: if quotes are missing or stale, fill is refused.

4. **`PaperOrderManager`** (`src/paper_trading/order_manager.py`):
   - Full lifecycle management (`PENDING`, `SUBMITTED`, `FILLED`, `PARTIALLY_FILLED`, `CANCELLED`, `REJECTED`, `EXPIRED`).
   - Idempotency key tracking to guarantee zero duplicate executions.

5. **`PaperRiskManager`** (`src/paper_trading/risk_manager.py`):
   - Pre-trade risk validation: max position size, max open orders, max daily loss limit, capital allocation.
   - Automatic and manual circuit breakers that freeze trading upon risk breach.
   - All risk limits explicitly marked as **CONFIGURED PAPER RISK LIMITS**.

6. **`PaperPortfolioTracker`** (`src/paper_trading/portfolio.py`):
   - Multi-asset position management (equity & index derivatives).
   - Realized and unrealized P&L calculations.
   - Genuine mark-to-market valuations; if live price is unavailable, price is marked `UNAVAILABLE` rather than interpolated.

7. **`PaperTradeJournal`** (`src/paper_trading/journal.py`):
   - Immutable audit logging of every order, fill, cancellation, rejection, and risk event.

8. **`PaperReconciliation`** (`src/paper_trading/reconciliation.py`):
   - Verifies portfolio equation: $\text{Starting Cash} + \text{Realized P\&L} - \text{Fees} = \text{Current Cash}$.
   - Asserts fill quantities match position holdings.
   - Flags discrepancies as `RECONCILIATION_FAILURE` without silent auto-correction.

---

## 3. Configuration

Configured in `config/settings.yaml`:
```yaml
paper_trading:
  enabled: true
  initial_capital: 1000000.0  # 10 Lakhs INR
  slippage_model: "square_root"
  default_slippage_bps: 5.0
  latency_ms: 50
  max_position_size_inr: 200000.0
  max_daily_loss_inr: 50000.0
  max_drawdown_pct: 0.10
  enforce_market_hours: true
```

---

## 4. API Endpoints

All endpoints are prefixed with `/api/v1/paper`:
- `GET /api/v1/paper/portfolio` — Portfolio equity, cash, open positions, drawdown.
- `GET /api/v1/paper/positions` — Filter open or closed paper positions.
- `POST /api/v1/paper/orders` — Place paper order (rejects live mode with 400).
- `GET /api/v1/paper/orders` — Query recent paper orders.
- `DELETE /api/v1/paper/orders/{order_id}` — Cancel a pending paper order.
- `GET /api/v1/paper/risk/status` — Risk metrics, circuit breaker states.
- `POST /api/v1/paper/reconcile` — Execute on-demand portfolio reconciliation.
- `GET /api/v1/paper/journal` — Retrieve audit trail events.
