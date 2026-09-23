"""
Phase 8 — Paper Trade Journal.

Records every decision, order, fill, rejection, cancellation, position change,
risk event, and portfolio snapshot for audit and analysis.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.paper_trading.models import (
    ExecutionRefusal,
    PaperFill,
    PaperOrder,
    PaperPortfolioSnapshot,
    PaperTradeRecord,
)


class PaperTradeJournal:
    """
    Audit journal for paper trading activity.
    Every execution attempt is recorded — fills, rejections, and risk events.
    """

    def __init__(self, output_dir: str = "data/paper_journals"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._entries: List[Dict[str, Any]] = []

    def record_order(self, order: PaperOrder) -> None:
        """Record an order event."""
        self._entries.append({
            "type": "ORDER",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "order_id": order.order_id,
            "symbol": order.symbol,
            "side": order.side.value,
            "quantity": order.quantity,
            "order_type": order.order_type.value,
            "status": order.status.value,
            "execution_mode": order.execution_mode,
            "rejection_reason": order.rejection_reason,
        })

    def record_fill(self, fill: PaperFill) -> None:
        """Record a fill event with full provenance."""
        self._entries.append({
            "type": "FILL",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fill_id": fill.fill_id,
            "order_id": fill.order_id,
            "symbol": fill.symbol,
            "fill_quantity": fill.fill_quantity,
            "fill_price": fill.fill_price,
            "provider_timestamp": fill.provider_timestamp.isoformat(),
            "data_status_at_fill": fill.data_status_at_fill,
            "source_provider": fill.source_provider,
            "price_source": fill.price_source.value,
            "slippage_applied": fill.slippage_applied,
            "transaction_costs": fill.transaction_costs,
            "quote_age_seconds": fill.quote_age_seconds,
            "execution_mode": fill.execution_mode,
        })

    def record_refusal(self, refusal: ExecutionRefusal) -> None:
        """Record an execution refusal."""
        self._entries.append({
            "type": "REFUSAL",
            "timestamp": refusal.timestamp.isoformat(),
            "order_id": refusal.order_id,
            "reason": refusal.reason,
            "details": refusal.details,
            "data_status": refusal.data_status,
            "market_status": refusal.market_status,
        })

    def record_cancellation(self, order_id: str, reason: str = "") -> None:
        """Record an order cancellation."""
        self._entries.append({
            "type": "CANCELLATION",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "order_id": order_id,
            "reason": reason,
        })

    def record_expiration(self, order_id: str) -> None:
        """Record an order expiration."""
        self._entries.append({
            "type": "EXPIRATION",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "order_id": order_id,
        })

    def record_risk_event(self, event: Dict[str, Any]) -> None:
        """Record a risk event (circuit breaker, limit breach)."""
        self._entries.append({
            "type": "RISK_EVENT",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **event,
        })

    def record_trade(self, trade: PaperTradeRecord) -> None:
        """Record a completed trade."""
        self._entries.append({
            "type": "TRADE",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trade_id": trade.trade_id,
            "symbol": trade.symbol,
            "direction": trade.direction,
            "quantity": trade.quantity,
            "entry_price": trade.entry_price,
            "exit_price": trade.exit_price,
            "net_pnl": trade.net_pnl,
            "fees": trade.fees,
            "slippage": trade.slippage,
            "holding_period_seconds": trade.holding_period_seconds,
            "evidence_label": trade.evidence_label,
            "execution_mode": trade.execution_mode,
        })

    def record_snapshot(self, snapshot: PaperPortfolioSnapshot) -> None:
        """Record a portfolio snapshot."""
        self._entries.append({
            "type": "SNAPSHOT",
            "timestamp": snapshot.timestamp.isoformat(),
            "cash": snapshot.cash,
            "equity": snapshot.equity,
            "realized_pnl": snapshot.realized_pnl,
            "unrealized_pnl": snapshot.unrealized_pnl,
            "drawdown_pct": snapshot.current_drawdown_pct,
            "open_positions": snapshot.open_positions_count,
            "execution_mode": snapshot.execution_mode,
        })

    def record_reset(self, session_id: str, reason: str = "USER_RESET") -> None:
        """Record a paper account reset event."""
        self._entries.append({
            "type": "RESET",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "reason": reason,
        })

    def get_entries(
        self,
        entry_type: Optional[str] = None,
        symbol: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Query journal entries with optional filters."""
        entries = self._entries
        if entry_type:
            entries = [e for e in entries if e.get("type") == entry_type]
        if symbol:
            entries = [e for e in entries if e.get("symbol") == symbol]
        if limit:
            entries = entries[-limit:]
        return entries

    def export_json(self, filename: str = "paper_journal.json") -> str:
        """Export journal to JSON."""
        filepath = self.output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self._entries, f, indent=2, default=str)
        return str(filepath)

    def export_csv(self, filename: str = "paper_journal.csv") -> str:
        """Export journal to CSV."""
        import csv
        filepath = self.output_dir / filename
        if not self._entries:
            return str(filepath)

        all_keys = set()
        for e in self._entries:
            all_keys.update(e.keys())
        fieldnames = sorted(all_keys)

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for entry in self._entries:
                writer.writerow(entry)
        return str(filepath)

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        """Clear entries (for testing). Does NOT delete exported files."""
        self._entries.clear()
