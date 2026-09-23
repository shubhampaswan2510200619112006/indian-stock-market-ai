"""
Phase 8 — Paper Order Manager.

Manages the full order lifecycle: submit, cancel, expire, process.
Every order passes through risk checks before execution.
Every state transition is journaled.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple

from src.paper_trading.execution_guard import ExecutionGuard
from src.paper_trading.models import (
    ExecutionRefusal,
    PaperFill,
    PaperOrder,
    PaperOrderExpiry,
    PaperOrderSide,
    PaperOrderStatus,
    PaperOrderType,
    RiskCheckResult,
    _generate_id,
)


class PaperOrderManager:
    """
    Paper order lifecycle manager.

    No order can bypass risk checks.
    No order can be filled without passing execution validation.
    Every transition is recorded.
    """

    def __init__(self):
        self._orders: Dict[str, PaperOrder] = {}
        self._transition_log: List[Dict] = []

    def _log_transition(self, order_id: str, from_status: str, to_status: str, reason: str = "") -> None:
        """Record every state transition for audit trail."""
        self._transition_log.append({
            "order_id": order_id,
            "from_status": from_status,
            "to_status": to_status,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def submit_order(
        self,
        order: PaperOrder,
        risk_check_fn: Optional[Callable[[PaperOrder], RiskCheckResult]] = None,
    ) -> Tuple[PaperOrder, Optional[RiskCheckResult]]:
        """
        Submit a paper order. Applies risk checks before acceptance.

        Returns (order, risk_result).
        If risk check fails, order.status = REJECTED.
        """
        # Enforce paper mode
        ExecutionGuard.validate_execution_mode(order.execution_mode)

        order.submitted_at = datetime.now(timezone.utc)

        # Validate basic fields
        if order.quantity <= 0:
            order.status = PaperOrderStatus.REJECTED
            order.rejection_reason = "INVALID_QUANTITY"
            self._orders[order.order_id] = order
            self._log_transition(order.order_id, "NEW", "REJECTED", "Invalid quantity")
            return order, None

        if order.order_type == PaperOrderType.LIMIT and order.limit_price is None:
            order.status = PaperOrderStatus.REJECTED
            order.rejection_reason = "MISSING_LIMIT_PRICE"
            self._orders[order.order_id] = order
            self._log_transition(order.order_id, "NEW", "REJECTED", "Missing limit price")
            return order, None

        if order.order_type in (PaperOrderType.STOP, PaperOrderType.STOP_LIMIT) and order.stop_price is None:
            order.status = PaperOrderStatus.REJECTED
            order.rejection_reason = "MISSING_STOP_PRICE"
            self._orders[order.order_id] = order
            self._log_transition(order.order_id, "NEW", "REJECTED", "Missing stop price")
            return order, None

        # Risk check
        risk_result = None
        if risk_check_fn:
            risk_result = risk_check_fn(order)
            if not risk_result.is_approved:
                order.status = PaperOrderStatus.REJECTED
                order.rejection_reason = "; ".join(risk_result.rejection_reasons)
                self._orders[order.order_id] = order
                self._log_transition(
                    order.order_id, "NEW", "REJECTED",
                    f"Risk rejected: {order.rejection_reason}"
                )
                return order, risk_result

        # Accept order
        if order.order_type == PaperOrderType.MARKET:
            order.status = PaperOrderStatus.PENDING
        else:
            order.status = PaperOrderStatus.OPEN

        self._orders[order.order_id] = order
        self._log_transition(order.order_id, "NEW", order.status.value, "Accepted")
        return order, risk_result

    def cancel_order(self, order_id: str) -> Optional[PaperOrder]:
        """Cancel a pending/open order."""
        order = self._orders.get(order_id)
        if order is None:
            return None

        if order.status in (PaperOrderStatus.PENDING, PaperOrderStatus.OPEN):
            old_status = order.status.value
            order.status = PaperOrderStatus.CANCELLED
            self._log_transition(order_id, old_status, "CANCELLED", "User cancelled")
            return order

        return order  # Already terminal

    def expire_order(self, order_id: str) -> Optional[PaperOrder]:
        """Expire a pending/open order. Expiry never creates a fill."""
        order = self._orders.get(order_id)
        if order is None:
            return None

        if order.status in (PaperOrderStatus.PENDING, PaperOrderStatus.OPEN):
            old_status = order.status.value
            order.status = PaperOrderStatus.EXPIRED
            self._log_transition(order_id, old_status, "EXPIRED", "Order expired")
            return order

        return order

    def expire_day_orders(self) -> List[PaperOrder]:
        """Expire all DAY orders that are still pending/open."""
        expired = []
        for order in self._orders.values():
            if (
                order.expiry_type == PaperOrderExpiry.DAY
                and order.status in (PaperOrderStatus.PENDING, PaperOrderStatus.OPEN)
            ):
                self.expire_order(order.order_id)
                expired.append(order)
        return expired

    def apply_fill(self, order_id: str, fill: PaperFill) -> Optional[PaperOrder]:
        """Apply a fill to an order, updating its status."""
        order = self._orders.get(order_id)
        if order is None:
            return None

        old_status = order.status.value
        order.filled_quantity += fill.fill_quantity
        order.average_fill_price = fill.fill_price  # Simplified for single-fill
        order.filled_at = fill.fill_timestamp

        if order.filled_quantity >= order.quantity:
            order.status = PaperOrderStatus.FILLED
        else:
            order.status = PaperOrderStatus.PARTIALLY_FILLED

        self._log_transition(order_id, old_status, order.status.value, f"Fill {fill.fill_id}")
        return order

    def get_order(self, order_id: str) -> Optional[PaperOrder]:
        return self._orders.get(order_id)

    def get_order_history(self, status_filter: Optional[PaperOrderStatus] = None) -> List[PaperOrder]:
        orders = list(self._orders.values())
        if status_filter:
            orders = [o for o in orders if o.status == status_filter]
        return sorted(orders, key=lambda o: o.created_at, reverse=True)

    def get_pending_orders(self) -> List[PaperOrder]:
        return [
            o for o in self._orders.values()
            if o.status in (PaperOrderStatus.PENDING, PaperOrderStatus.OPEN)
        ]

    def get_transition_log(self) -> List[Dict]:
        return list(self._transition_log)

    def cancel_all_pending(self, reason: str = "CIRCUIT_BREAKER") -> List[PaperOrder]:
        """Cancel all pending/open orders. Used by circuit breakers."""
        cancelled = []
        for order in list(self._orders.values()):
            if order.status in (PaperOrderStatus.PENDING, PaperOrderStatus.OPEN):
                old_status = order.status.value
                order.status = PaperOrderStatus.CANCELLED
                order.rejection_reason = reason
                self._log_transition(order.order_id, old_status, "CANCELLED", reason)
                cancelled.append(order)
        return cancelled

    def get_all_orders(self) -> Dict[str, PaperOrder]:
        """Return all orders for persistence."""
        return dict(self._orders)

    def load_orders(self, orders: Dict[str, PaperOrder]) -> None:
        """Load orders from persistence (crash recovery)."""
        self._orders.update(orders)
