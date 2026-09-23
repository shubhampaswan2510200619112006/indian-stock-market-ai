"""
Phase 8 — Paper Portfolio Tracker.

Tracks cash, positions, P&L, drawdown, and Greeks for the paper trading account.
Mark-to-market uses only genuine provider observations.
If market price is unavailable: MARK UNAVAILABLE (never fabricated).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from src.paper_trading.models import (
    PaperFill,
    PaperOrderSide,
    PaperPortfolioSnapshot,
    PaperPosition,
    PaperTradeRecord,
    _generate_id,
)


class PaperPortfolioTracker:
    """
    Paper portfolio tracker with position management and mark-to-market.

    Starting capital is a CONFIGURED PAPER CAPITAL, not a recommendation.
    """

    def __init__(self, initial_capital: float = 1_000_000.0, session_id: Optional[str] = None):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.session_id = session_id

        self._positions: Dict[str, PaperPosition] = {}
        self._closed_trades: List[PaperTradeRecord] = []
        self._snapshots: List[PaperPortfolioSnapshot] = []

        self.realized_pnl: float = 0.0
        self.peak_equity: float = initial_capital
        self.max_drawdown_pct: float = 0.0
        self.daily_starting_equity: float = initial_capital

    def apply_fill(self, fill: PaperFill, side: PaperOrderSide, lot_size: int = 1) -> Optional[PaperTradeRecord]:
        """
        Apply a fill to the portfolio. Opens/updates/closes positions.

        Returns a PaperTradeRecord if a position was closed, else None.
        """
        symbol = fill.symbol
        total_cost = fill.fill_price * fill.fill_quantity
        trade_record = None

        if symbol in self._positions and self._positions[symbol].is_open:
            pos = self._positions[symbol]
            existing_direction = "LONG" if pos.quantity > 0 else "SHORT"
            fill_direction = "LONG" if side == PaperOrderSide.BUY else "SHORT"

            if existing_direction == fill_direction:
                # Increase position
                old_total = pos.average_entry_price * abs(pos.quantity)
                new_total = fill.fill_price * fill.fill_quantity

                if side == PaperOrderSide.BUY:
                    pos.quantity += fill.fill_quantity
                else:
                    pos.quantity -= fill.fill_quantity

                abs_qty = abs(pos.quantity)
                if abs_qty > 0:
                    pos.average_entry_price = (old_total + new_total) / abs_qty

                # Deduct/add cash
                if side == PaperOrderSide.BUY:
                    self.cash -= (total_cost + fill.transaction_costs)
                else:
                    self.cash += (total_cost - fill.transaction_costs)

            else:
                # Reduce/close/reverse position
                close_qty = min(abs(pos.quantity), fill.fill_quantity)
                remaining_fill_qty = fill.fill_quantity - close_qty

                # Calculate realized P&L for closed portion
                if existing_direction == "LONG":
                    pnl = (fill.fill_price - pos.average_entry_price) * close_qty
                else:
                    pnl = (pos.average_entry_price - fill.fill_price) * close_qty

                pnl -= fill.transaction_costs
                self.realized_pnl += pnl

                # Update cash
                if side == PaperOrderSide.BUY:
                    self.cash -= (fill.fill_price * fill.fill_quantity + fill.transaction_costs)
                else:
                    self.cash += (fill.fill_price * fill.fill_quantity - fill.transaction_costs)

                # Create trade record for closed portion
                trade_record = PaperTradeRecord(
                    session_id=self.session_id,
                    symbol=symbol,
                    strategy=pos.strategy,
                    direction=existing_direction,
                    entry_timestamp=pos.entry_timestamp or fill.fill_timestamp,
                    exit_timestamp=fill.fill_timestamp,
                    quantity=close_qty,
                    entry_price=pos.average_entry_price,
                    exit_price=fill.fill_price,
                    gross_pnl=round(pnl + fill.transaction_costs, 2),
                    fees=fill.transaction_costs,
                    slippage=fill.slippage_applied * close_qty,
                    net_pnl=round(pnl, 2),
                    holding_period_seconds=(fill.fill_timestamp - (pos.entry_timestamp or fill.fill_timestamp)).total_seconds(),
                )
                self._closed_trades.append(trade_record)

                # Update position quantity
                if existing_direction == "LONG":
                    pos.quantity -= close_qty
                else:
                    pos.quantity += close_qty

                # If reversed, open new position with remaining
                if remaining_fill_qty > 0:
                    new_direction_qty = remaining_fill_qty if side == PaperOrderSide.BUY else -remaining_fill_qty
                    pos.quantity = new_direction_qty
                    pos.average_entry_price = fill.fill_price
                    pos.entry_timestamp = fill.fill_timestamp

                if pos.quantity == 0:
                    pos.realized_pnl += pnl
                    # Keep position record but it's closed
        else:
            # Open new position
            qty = fill.fill_quantity if side == PaperOrderSide.BUY else -fill.fill_quantity

            pos = PaperPosition(
                symbol=symbol,
                instrument_type="INDEX",
                quantity=qty,
                average_entry_price=fill.fill_price,
                entry_timestamp=fill.fill_timestamp,
            )
            self._positions[symbol] = pos

            # Deduct/add cash
            if side == PaperOrderSide.BUY:
                self.cash -= (total_cost + fill.transaction_costs)
            else:
                self.cash += (total_cost - fill.transaction_costs)

        return trade_record

    def mark_to_market(
        self,
        symbol: str,
        current_price: Optional[float],
        mark_timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Mark a position to current market price.
        If current_price is None → MARK UNAVAILABLE (never fabricated).
        """
        pos = self._positions.get(symbol)
        if pos is None or not pos.is_open:
            return

        if current_price is not None and current_price > 0:
            pos.current_market_price = current_price
            pos.last_mark_timestamp = mark_timestamp or datetime.now(timezone.utc)
            pos.last_mark_status = "MARKET_PRICE"

            abs_qty = abs(pos.quantity)
            pos.market_value = current_price * abs_qty

            if pos.quantity > 0:  # Long
                pos.unrealized_pnl = (current_price - pos.average_entry_price) * abs_qty
            else:  # Short
                pos.unrealized_pnl = (pos.average_entry_price - current_price) * abs_qty
        else:
            pos.last_mark_status = "MARK_UNAVAILABLE"
            pos.unrealized_pnl = None
            pos.market_value = None

    def get_equity(self) -> float:
        """Calculate total equity = cash + market value of all positions."""
        total_market_value = 0.0
        for pos in self._positions.values():
            if pos.is_open:
                if pos.quantity > 0:
                    val = pos.market_value if pos.market_value is not None else (pos.average_entry_price * pos.quantity)
                    total_market_value += val
                else:
                    val = pos.market_value if pos.market_value is not None else (pos.average_entry_price * abs(pos.quantity))
                    total_market_value -= val
        return self.cash + total_market_value

    def get_unrealized_pnl(self) -> Optional[float]:
        """Total unrealized P&L. None if any position has MARK UNAVAILABLE."""
        total = 0.0
        for pos in self._positions.values():
            if pos.is_open:
                if pos.unrealized_pnl is None:
                    return None
                total += pos.unrealized_pnl
        return total

    def get_drawdown(self) -> float:
        """Current drawdown percentage from peak equity."""
        equity = self.get_equity()
        if equity > self.peak_equity:
            self.peak_equity = equity
        if self.peak_equity > 0:
            dd = (self.peak_equity - equity) / self.peak_equity
            self.max_drawdown_pct = max(self.max_drawdown_pct, dd)
            return dd
        return 0.0

    def get_daily_pnl(self) -> float:
        """Calculate daily P&L from daily starting equity."""
        return self.get_equity() - self.daily_starting_equity

    def reset_daily(self) -> None:
        """Reset daily tracking at start of new trading day."""
        self.daily_starting_equity = self.get_equity()

    def take_snapshot(self) -> PaperPortfolioSnapshot:
        """Create a point-in-time portfolio snapshot."""
        equity = self.get_equity()
        unrealized = self.get_unrealized_pnl()
        drawdown = self.get_drawdown()

        open_count = sum(1 for p in self._positions.values() if p.is_open)
        gross_exposure = sum(
            abs(p.quantity) * (p.current_market_price or p.average_entry_price)
            for p in self._positions.values() if p.is_open
        )

        snap = PaperPortfolioSnapshot(
            session_id=self.session_id,
            cash=round(self.cash, 2),
            equity=round(equity, 2),
            available_cash=round(self.cash, 2),
            realized_pnl=round(self.realized_pnl, 2),
            unrealized_pnl=round(unrealized, 2) if unrealized is not None else 0.0,
            total_pnl=round(self.realized_pnl + (unrealized or 0.0), 2),
            daily_pnl=round(self.get_daily_pnl(), 2),
            peak_equity=round(self.peak_equity, 2),
            current_drawdown_pct=round(drawdown, 6),
            max_drawdown_pct=round(self.max_drawdown_pct, 6),
            open_positions_count=open_count,
            gross_exposure=round(gross_exposure, 2),
        )
        self._snapshots.append(snap)
        return snap

    def get_positions(self) -> List[PaperPosition]:
        return list(self._positions.values())

    def get_open_positions(self) -> List[PaperPosition]:
        return [p for p in self._positions.values() if p.is_open]

    def get_closed_trades(self) -> List[PaperTradeRecord]:
        return list(self._closed_trades)

    def get_snapshots(self) -> List[PaperPortfolioSnapshot]:
        return list(self._snapshots)

    def get_position(self, symbol: str) -> Optional[PaperPosition]:
        return self._positions.get(symbol)

    def reset(self, new_capital: Optional[float] = None) -> None:
        """Reset portfolio to initial state. Preserves closed trade history."""
        capital = new_capital or self.initial_capital
        self.initial_capital = capital
        self.cash = capital
        self._positions.clear()
        self.realized_pnl = 0.0
        self.peak_equity = capital
        self.max_drawdown_pct = 0.0
        self.daily_starting_equity = capital

    def get_state(self) -> Dict[str, Any]:
        """Serialize portfolio state for crash recovery."""
        return {
            "initial_capital": self.initial_capital,
            "cash": self.cash,
            "session_id": self.session_id,
            "realized_pnl": self.realized_pnl,
            "peak_equity": self.peak_equity,
            "max_drawdown_pct": self.max_drawdown_pct,
            "daily_starting_equity": self.daily_starting_equity,
            "positions": {sym: pos.model_dump(mode="json") for sym, pos in self._positions.items()},
            "closed_trades": [t.model_dump(mode="json") for t in self._closed_trades],
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        """Load portfolio state for crash recovery."""
        self.initial_capital = state.get("initial_capital", self.initial_capital)
        self.cash = state.get("cash", self.cash)
        self.session_id = state.get("session_id", self.session_id)
        self.realized_pnl = state.get("realized_pnl", 0.0)
        self.peak_equity = state.get("peak_equity", self.cash)
        self.max_drawdown_pct = state.get("max_drawdown_pct", 0.0)
        self.daily_starting_equity = state.get("daily_starting_equity", self.cash)

        self._positions.clear()
        for sym, p_dict in state.get("positions", {}).items():
            self._positions[sym] = PaperPosition(**p_dict)

        self._closed_trades.clear()
        for t_dict in state.get("closed_trades", []):
            self._closed_trades.append(PaperTradeRecord(**t_dict))
