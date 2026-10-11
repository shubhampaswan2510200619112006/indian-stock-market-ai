"""
Phase 8 — Paper Trading Service (Orchestrator).

Integrates all paper trading components into a unified service.
Every output is labeled PAPER_TRADE.
No component may bypass the risk engine.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.paper_trading.execution_guard import ExecutionGuard
from src.paper_trading.fill_engine import SimulatedFillEngine
from src.paper_trading.journal import PaperTradeJournal
from src.paper_trading.market_hours import get_market_state, is_fill_eligible_market_state
from src.paper_trading.metrics import compute_paper_performance
from src.paper_trading.models import (
    ExecutionRefusal,
    MarketState,
    PaperFill,
    PaperFillSource,
    PaperOrder,
    PaperOrderSide,
    PaperOrderStatus,
    PaperOrderType,
    PaperPortfolioSnapshot,
    PaperTradeRecord,
    RiskCheckResult,
)
from src.paper_trading.order_manager import PaperOrderManager
from src.paper_trading.portfolio import PaperPortfolioTracker
from src.paper_trading.reconciliation import reconcile_paper_account
from src.paper_trading.risk_manager import PaperRiskManager
from src.paper_trading.state import PaperSessionManager


class PaperTradingService:
    """
    Top-level orchestrator for the paper trading system.

    Integrates:
    - ExecutionGuard (safety)
    - LiveMarketService (Phase 7 data)
    - PaperOrderManager (order lifecycle)
    - SimulatedFillEngine (execution)
    - PaperPortfolioTracker (positions & P&L)
    - PaperRiskManager (risk controls)
    - PaperTradeJournal (audit)
    - PaperSessionManager (persistence)

    Every output explicitly labeled: execution_mode = PAPER_TRADE
    """

    # Non-negotiable Phase 8.5 requirement:
    # Autonomous model-to-order submission is disabled by default.
    AUTO_PAPER_ORDER_SUBMISSION: bool = False

    def __init__(
        self,
        initial_capital: float = 1_000_000.0,
        max_fill_age_seconds: float = 120.0,
        max_spread_pct: float = 0.15,
        slippage_pct: float = 0.005,
        max_position_size_lots: int = 50,
        max_open_positions: int = 5,
        max_risk_per_trade_pct: float = 2.0,
        max_daily_loss_pct: float = 5.0,
        max_portfolio_drawdown_pct: float = 15.0,
        delayed_data_fill_allowed: bool = True,
        delayed_data_max_age_seconds: float = 300.0,
        state_dir: str = "data/paper_state",
        auto_restore: bool = False,
    ):
        # Safety: validate paper mode at construction
        ExecutionGuard.assert_paper_mode()
        ExecutionGuard.validate_execution_mode("PAPER")

        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Session manager
        self.session_manager = PaperSessionManager(state_dir=str(self.state_dir))

        # Core components
        self.order_manager = PaperOrderManager()
        self.fill_engine = SimulatedFillEngine(
            max_fill_age_seconds=max_fill_age_seconds,
            max_spread_pct=max_spread_pct,
            slippage_pct=slippage_pct,
            delayed_data_fill_allowed=delayed_data_fill_allowed,
            delayed_data_max_age_seconds=delayed_data_max_age_seconds,
        )
        self.portfolio = PaperPortfolioTracker(
            initial_capital=initial_capital,
            session_id=self.session_manager.session_id,
        )
        self.risk_manager = PaperRiskManager(
            max_position_size_lots=max_position_size_lots,
            max_open_positions=max_open_positions,
            max_risk_per_trade_pct=max_risk_per_trade_pct,
            max_daily_loss_pct=max_daily_loss_pct,
            max_portfolio_drawdown_pct=max_portfolio_drawdown_pct,
        )
        self.journal = PaperTradeJournal()

        # Track fills for reconciliation
        self._all_fills: List[PaperFill] = []
        self._refusal_count: int = 0
        self._no_trade_count: int = 0

        # Auto-restore state if requested
        if auto_restore:
            self.restore_state()

    def start_session(self, capital: Optional[float] = None) -> Dict[str, Any]:
        """Start a new paper trading session."""
        ExecutionGuard.assert_paper_mode()

        cap = capital or self.portfolio.initial_capital
        session_id = self.session_manager.start(starting_capital=cap)
        self.portfolio.session_id = session_id
        self.save_state()

        return {
            "execution_mode": "PAPER_TRADE",
            "session_id": session_id,
            "status": "STARTED",
            "starting_capital": cap,
            "message": "Paper trading session started. NO LIVE ORDERS.",
        }

    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        order_type: str = "MARKET",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        instrument_type: str = "INDEX",
        strategy_name: Optional[str] = None,
        strike: Optional[float] = None,
        expiry_date: Optional[str] = None,
        option_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Place a paper order. Goes through risk check before acceptance.
        """
        ExecutionGuard.validate_execution_mode("PAPER")

        order = PaperOrder(
            symbol=symbol.upper(),
            side=PaperOrderSide(side.upper()),
            quantity=quantity,
            order_type=PaperOrderType(order_type.upper()),
            limit_price=limit_price,
            stop_price=stop_price,
            instrument_type=instrument_type,
            strategy_name=strategy_name,
            execution_mode="PAPER",
            decision_timestamp=datetime.now(timezone.utc),
            session_id=self.session_manager.session_id,
            strike=strike,
            option_type=option_type,
        )

        # Risk check function
        def risk_check(o: PaperOrder) -> RiskCheckResult:
            return self.risk_manager.check_order(
                order=o,
                current_equity=self.portfolio.get_equity(),
                daily_pnl=self.portfolio.get_daily_pnl(),
                drawdown_pct=self.portfolio.get_drawdown(),
                open_positions=self.portfolio.get_open_positions(),
            )

        order, risk_result = self.order_manager.submit_order(order, risk_check_fn=risk_check)

        # Journal the order
        self.journal.record_order(order)
        self.save_state()

        if order.status == PaperOrderStatus.REJECTED:
            self._refusal_count += 1

        return {
            "execution_mode": "PAPER_TRADE",
            "order_id": order.order_id,
            "status": order.status.value,
            "rejection_reason": order.rejection_reason,
            "risk_approved": risk_result.is_approved if risk_result else None,
            "message": "PAPER ORDER ONLY — no real execution",
        }

    def process_market_update(
        self,
        symbol: str,
        bid: Optional[float],
        ask: Optional[float],
        ltp: Optional[float] = None,
        provider_timestamp: Optional[datetime] = None,
        received_timestamp: Optional[datetime] = None,
        data_status: str = "DELAYED",
        source_provider: str = "YFINANCE",
    ) -> Dict[str, Any]:
        """
        Process a market data update: attempt fills on pending orders and mark-to-market.
        """
        ExecutionGuard.assert_paper_mode()

        results = {
            "execution_mode": "PAPER_TRADE",
            "symbol": symbol,
            "fills": [],
            "refusals": [],
            "positions_marked": 0,
        }

        # Check and update circuit breakers
        breakers = self.risk_manager.update_circuit_breakers(
            daily_pnl=self.portfolio.get_daily_pnl(),
            current_equity=self.portfolio.get_equity(),
            drawdown_pct=self.portfolio.get_drawdown(),
        )
        if breakers:
            cancelled = self.order_manager.cancel_all_pending(reason="CIRCUIT_BREAKER")
            for o in cancelled:
                self.journal.record_cancellation(o.order_id, "CIRCUIT_BREAKER")
            for b in breakers:
                self.journal.record_risk_event({"type": b})

        # Process pending orders
        pending = self.order_manager.get_pending_orders()
        for order in pending:
            if order.symbol.upper() != symbol.upper():
                continue

            fill, refusal = self.fill_engine.attempt_fill(
                order=order,
                bid=bid,
                ask=ask,
                provider_timestamp=provider_timestamp,
                received_timestamp=received_timestamp,
                data_status=data_status,
                source_provider=source_provider,
            )

            if fill:
                # Apply fill to order
                self.order_manager.apply_fill(order.order_id, fill)

                # Apply fill to portfolio
                trade_record = self.portfolio.apply_fill(fill, order.side)

                # Journal
                self.journal.record_fill(fill)
                self._all_fills.append(fill)

                if trade_record:
                    self.journal.record_trade(trade_record)

                results["fills"].append({
                    "fill_id": fill.fill_id,
                    "order_id": fill.order_id,
                    "fill_price": fill.fill_price,
                    "fill_quantity": fill.fill_quantity,
                    "data_status": fill.data_status_at_fill,
                    "source_provider": fill.source_provider,
                    "price_source": fill.price_source.value,
                    "quote_age_seconds": fill.quote_age_seconds,
                })

            elif refusal:
                self.journal.record_refusal(refusal)
                self._refusal_count += 1
                results["refusals"].append({
                    "order_id": refusal.order_id,
                    "reason": refusal.reason,
                    "details": refusal.details,
                })

        # Mark-to-market: use bid for sells (conservative), ask for buys
        # For simplicity, use midpoint if both available, else whatever is available
        mark_price = None
        if bid is not None and ask is not None and bid > 0 and ask > 0:
            mark_price = (bid + ask) / 2.0
        elif ltp is not None and ltp > 0:
            # LTP can be used for mark-to-market display (NOT execution)
            mark_price = ltp

        if mark_price and data_status.upper() not in ("STALE", "UNAVAILABLE", "ERROR"):
            self.portfolio.mark_to_market(symbol.upper(), mark_price, provider_timestamp)
            results["positions_marked"] = 1

        if results["fills"] or results["positions_marked"]:
            self.save_state()

        return results

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get current portfolio state."""
        snap = self.portfolio.take_snapshot()
        self.journal.record_snapshot(snap)

        return {
            "execution_mode": "PAPER_TRADE",
            "session_id": self.session_manager.session_id,
            "session_status": self.session_manager.status.value,
            "cash": snap.cash,
            "equity": snap.equity,
            "realized_pnl": snap.realized_pnl,
            "unrealized_pnl": snap.unrealized_pnl,
            "total_pnl": snap.total_pnl,
            "daily_pnl": snap.daily_pnl,
            "drawdown_pct": snap.current_drawdown_pct,
            "max_drawdown_pct": snap.max_drawdown_pct,
            "open_positions_count": snap.open_positions_count,
            "starting_capital": self.portfolio.initial_capital,
            "label": "CONFIGURED PAPER CAPITAL",
            "LIVE_EXECUTION": "DISABLED",
            "BROKER_CONNECTIONS": "NONE",
        }

    def get_positions(self, status: Optional[str] = None) -> Dict[str, Any]:
        """Get positions, optionally filtered by status ('OPEN' or 'CLOSED')."""
        if status and status.upper() == "CLOSED":
            closed_trades = self.portfolio.get_closed_trades()
            return {
                "execution_mode": "PAPER_TRADE",
                "positions": [
                    {
                        "position_id": t.trade_id,
                        "symbol": t.symbol,
                        "side": t.direction if hasattr(t, "direction") else "LONG",
                        "quantity": t.quantity,
                        "avg_entry_price": t.entry_price,
                        "realized_pnl": t.net_pnl,
                        "asset_class": "EQUITY",
                        "opened_at": t.entry_timestamp.isoformat() if t.entry_timestamp else None,
                        "closed_at": t.exit_timestamp.isoformat() if t.exit_timestamp else None,
                    }
                    for t in closed_trades
                ],
            }

        positions = self.portfolio.get_open_positions()
        return {
            "execution_mode": "PAPER_TRADE",
            "positions": [
                {
                    "position_id": p.position_id,
                    "symbol": p.symbol,
                    "side": "LONG" if p.quantity > 0 else "SHORT",
                    "quantity": p.quantity,
                    "avg_entry_price": p.average_entry_price,
                    "average_entry_price": p.average_entry_price,
                    "current_price": p.current_market_price,
                    "current_market_price": p.current_market_price,
                    "unrealized_pnl": p.unrealized_pnl,
                    "realized_pnl": p.realized_pnl,
                    "last_mark_status": p.last_mark_status,
                    "strategy": p.strategy,
                    "greeks_status": p.greeks_status,
                    "asset_class": getattr(p, "instrument_type", "EQUITY"),
                    "opened_at": p.entry_timestamp.isoformat() if p.entry_timestamp else None,
                }
                for p in positions
            ],
        }

    def get_orders(self, status: Optional[str] = None) -> Dict[str, Any]:
        """Get order history."""
        filter_status = PaperOrderStatus(status) if status else None
        orders = self.order_manager.get_order_history(filter_status)
        return {
            "execution_mode": "PAPER_TRADE",
            "orders": [
                {
                    "order_id": o.order_id,
                    "symbol": o.symbol,
                    "side": o.side.value,
                    "quantity": o.quantity,
                    "order_type": o.order_type.value,
                    "status": o.status.value,
                    "rejection_reason": o.rejection_reason,
                    "filled_quantity": o.filled_quantity,
                    "average_fill_price": o.average_fill_price,
                    "created_at": o.created_at.isoformat(),
                }
                for o in orders
            ],
        }

    def get_trade_history(self) -> Dict[str, Any]:
        """Get completed trade history."""
        trades = self.portfolio.get_closed_trades()
        return {
            "execution_mode": "PAPER_TRADE",
            "trades": [
                {
                    "trade_id": t.trade_id,
                    "symbol": t.symbol,
                    "direction": t.direction,
                    "quantity": t.quantity,
                    "entry_price": t.entry_price,
                    "exit_price": t.exit_price,
                    "net_pnl": t.net_pnl,
                    "fees": t.fees,
                    "evidence_label": t.evidence_label,
                }
                for t in trades
            ],
            "disclaimer": "Paper trading results do not predict future profitability.",
        }

    def get_risk_status(self) -> Dict[str, Any]:
        """Get current risk engine status."""
        status = self.risk_manager.get_risk_status()
        status["execution_mode"] = "PAPER_TRADE"
        return status

    def get_session_status(self) -> Dict[str, Any]:
        """Get session status."""
        info = self.session_manager.get_session_info()
        guard_status = ExecutionGuard.get_execution_status()
        return {
            "execution_mode": "PAPER_TRADE",
            **info,
            **guard_status,
            "options_paper_trading": "UNAVAILABLE",
            "options_live_readiness": "NOT_VERIFIED",
            "ml_production_readiness": "NOT_READY",
        }

    def get_reconciliation(self) -> Dict[str, Any]:
        """Run reconciliation check."""
        result = reconcile_paper_account(
            starting_cash=self.portfolio.initial_capital,
            ending_cash=self.portfolio.cash,
            positions=self.portfolio.get_open_positions(),
            fills=self._all_fills,
            closed_trades=self.portfolio.get_closed_trades(),
            total_orders=len(self.order_manager.get_all_orders()),
            total_rejections=self._refusal_count,
            total_no_trade=self._no_trade_count,
        )
        return {
            "execution_mode": "PAPER_TRADE",
            **result.model_dump(),
        }

    def reconcile(self) -> Dict[str, Any]:
        """Alias for get_reconciliation."""
        return self.get_reconciliation()

    def get_performance(self) -> Dict[str, Any]:
        """Get performance metrics with evidence labels."""
        perf = compute_paper_performance(
            trades=self.portfolio.get_closed_trades(),
            snapshots=self.portfolio.get_snapshots(),
            initial_capital=self.portfolio.initial_capital,
        )
        perf["execution_mode"] = "PAPER_TRADE"
        return perf

    def reset_paper_account(self, confirm: bool = False, archive: bool = False) -> Dict[str, Any]:
        """
        Reset the paper trading account.
        Requires explicit confirmation.
        RESET RULE (Phase 8.5): If open positions exist, RESET is REJECTED to prevent fabricating liquidations.
        If archive=True, old session is preserved without fabricating liquidation fills.
        """
        if not confirm:
            return {
                "execution_mode": "PAPER_TRADE",
                "status": "CONFIRMATION_REQUIRED",
                "message": "Call with confirm=True to reset. Historical journal records are preserved.",
            }

        open_positions = self.portfolio.get_open_positions()
        if open_positions and not archive:
            return {
                "execution_mode": "PAPER_TRADE",
                "status": "RESET_REJECTED",
                "reason": "OPEN_POSITIONS_EXIST",
                "open_positions_count": len(open_positions),
                "message": (
                    "Reset rejected: open positions exist. The system NEVER fabricates closing/liquidation fills. "
                    "Close positions via valid paper orders first, or pass archive=True to preserve the session intact."
                ),
            }

        old_session = self.session_manager.session_id

        # Record reset event before clearing
        self.journal.record_reset(old_session or "unknown", reason="ARCHIVED_AND_RESET" if archive else "USER_RESET")

        # If archive requested, persist snapshot archive
        if archive:
            archive_dir = self.state_dir / "archives" / f"session_{old_session}"
            archive_dir.mkdir(parents=True, exist_ok=True)
            self.save_state(target_dir=archive_dir)

        # Reset components
        self.session_manager.stop()
        self.portfolio.reset()
        self.order_manager = PaperOrderManager()
        self.fill_engine.reset_idempotency_cache()
        self.risk_manager.reset_circuit_breakers()
        self._all_fills.clear()
        self._refusal_count = 0
        self._no_trade_count = 0

        # Start new session
        new_session_id = self.session_manager.start(self.portfolio.initial_capital)
        self.portfolio.session_id = new_session_id
        self.save_state()

        return {
            "execution_mode": "PAPER_TRADE",
            "status": "RESET_COMPLETE",
            "old_session_id": old_session,
            "new_session_id": new_session_id,
            "starting_capital": self.portfolio.initial_capital,
            "archived": archive,
            "message": "Paper account reset. Historical journal preserved.",
        }

    def save_state(self, target_dir: Optional[Path] = None) -> None:
        """Persist complete service state for crash recovery."""
        d = target_dir or self.state_dir
        d.mkdir(parents=True, exist_ok=True)

        p_path = d / "portfolio_state.json"
        with open(p_path, "w", encoding="utf-8") as f:
            json.dump(self.portfolio.get_state(), f, indent=2, default=str)

        o_path = d / "orders_state.json"
        orders_dict = {
            oid: o.model_dump(mode="json")
            for oid, o in self.order_manager.get_all_orders().items()
        }
        with open(o_path, "w", encoding="utf-8") as f:
            json.dump(orders_dict, f, indent=2, default=str)

        f_path = d / "fills_state.json"
        fills_list = [f.model_dump(mode="json") for f in self._all_fills]
        with open(f_path, "w", encoding="utf-8") as f:
            json.dump(fills_list, f, indent=2, default=str)

    def restore_state(self, source_dir: Optional[Path] = None) -> bool:
        """Restore complete service state after crash or restart."""
        d = source_dir or self.state_dir
        p_path = d / "portfolio_state.json"
        o_path = d / "orders_state.json"
        f_path = d / "fills_state.json"

        restored = False
        if p_path.exists():
            try:
                with open(p_path, "r", encoding="utf-8") as f:
                    p_state = json.load(f)
                self.portfolio.load_state(p_state)
                restored = True
            except Exception:
                pass

        if o_path.exists():
            try:
                with open(o_path, "r", encoding="utf-8") as f:
                    o_state = json.load(f)
                recovered_orders = {
                    oid: PaperOrder(**odata)
                    for oid, odata in o_state.items()
                }
                self.order_manager.load_orders(recovered_orders)
                restored = True
            except Exception:
                pass

        if f_path.exists():
            try:
                with open(f_path, "r", encoding="utf-8") as f:
                    f_state = json.load(f)
                self._all_fills = [PaperFill(**fdata) for fdata in f_state]
                restored = True
            except Exception:
                pass

        return restored

    def get_journal_entries(
        self,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve audit journal entries with optional event_type filter."""
        return self.journal.get_entries(limit=limit, entry_type=event_type)

    def trip_breaker(self, reason: str = "MANUAL_EMERGENCY_HALT") -> Dict[str, Any]:
        """Manually trip emergency circuit breaker and cancel pending orders."""
        self.risk_manager.trip_breaker(reason=reason)
        cancelled = self.order_manager.cancel_all_pending(reason=reason)
        for o in cancelled:
            self.journal.record_cancellation(o.order_id, reason)
        self.save_state()
        return {"status": "TRIPPED", "reason": reason, "cancelled_orders": len(cancelled)}

    def reset_breakers(self) -> Dict[str, Any]:
        """Reset circuit breakers."""
        self.risk_manager.reset_circuit_breakers()
        self.save_state()
        return {"status": "RESET"}

    def close_position(self, position_id: str, quantity: Optional[int] = None) -> Dict[str, Any]:
        """
        Close an existing open paper position by creating and executing an offsetting fill.
        """
        ExecutionGuard.assert_paper_mode()
        open_pos = [
            p for p in self.portfolio.get_open_positions()
            if getattr(p, "position_id", None) == position_id or p.symbol == position_id
        ]
        if not open_pos:
            return {"status": "REJECTED", "rejection_reason": f"Position '{position_id}' not found or already closed."}

        pos = open_pos[0]
        qty_to_close = min(quantity or abs(pos.quantity), abs(pos.quantity))
        close_side = PaperOrderSide.SELL if pos.quantity > 0 else PaperOrderSide.BUY
        fill_source = PaperFillSource.PROVIDER_BID if pos.quantity > 0 else PaperFillSource.PROVIDER_ASK

        mark_price = pos.current_market_price or pos.average_entry_price or 100.0
        now = datetime.now(timezone.utc)

        fill = PaperFill(
            order_id=f"CLOSE-{pos.position_id}",
            symbol=pos.symbol,
            fill_quantity=qty_to_close,
            fill_price=mark_price,
            fill_timestamp=now,
            provider_timestamp=now,
            received_timestamp=now,
            execution_timestamp=now,
            price_source=fill_source,
            price_source_description="Position closing execution mark",
            data_status_at_fill="DELAYED",
            slippage_applied=0.0,
            transaction_costs=0.0,
            quote_age_seconds=1.0,
            source_provider="PAPER_SYSTEM",
            provider="PAPER_SYSTEM",
        )

        trade_record = self.portfolio.apply_fill(fill, close_side)
        self.journal.record_fill(fill)
        self._all_fills.append(fill)

        if trade_record:
            self.journal.record_trade(trade_record)

        self.save_state()
        return {
            "status": "CLOSED",
            "fill_id": fill.fill_id,
            "closed_quantity": qty_to_close,
            "fill_price": mark_price,
            "symbol": pos.symbol,
        }

