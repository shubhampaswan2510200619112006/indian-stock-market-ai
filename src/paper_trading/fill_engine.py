"""
Phase 8 — Simulated Fill Engine.

HARD INVARIANTS:
1. Market BUY fills ONLY from genuine current ASK — NEVER LTP.
2. Market SELL fills ONLY from genuine current BID — NEVER LTP.
3. If Bid/Ask is missing → EXECUTION REFUSED (no substitution).
4. STALE data → REJECT. UNAVAILABLE → REJECT. ERROR → REJECT.
5. No retroactive fills — only current-cycle observations trigger fills.
6. Every fill has complete provenance or is rejected.
7. Idempotent — same observation processed twice → exactly one fill.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Optional, Set, Tuple

from src.backtesting.execution import calculate_nse_option_transaction_costs
from src.backtesting.models import ExecutionCostModel
from src.live_market.models import RealTimeDataStatus
from src.paper_trading.execution_guard import ExecutionGuard
from src.paper_trading.market_hours import is_fill_eligible_market_state
from src.paper_trading.models import (
    ExecutionRefusal,
    PaperFill,
    PaperFillSource,
    PaperOrder,
    PaperOrderSide,
    PaperOrderType,
    PaperOrderStatus,
)
from src.utils.time_utils import now_ist


# Statuses that NEVER produce fills
_REJECT_STATUSES = {
    RealTimeDataStatus.STALE.value,
    RealTimeDataStatus.UNAVAILABLE.value,
    RealTimeDataStatus.ERROR.value,
    "STALE",
    "UNAVAILABLE",
    "ERROR",
}

# Statuses eligible for fills (subject to age check)
_ALLOWED_STATUSES = {
    RealTimeDataStatus.REAL_TIME.value,
    RealTimeDataStatus.NEAR_REAL_TIME.value,
    RealTimeDataStatus.DELAYED.value,
    "REAL_TIME",
    "NEAR_REAL_TIME",
    "DELAYED",
}


class SimulatedFillEngine:
    """
    Simulated execution engine for paper trading.

    NEVER fabricates a fill. Every fill requires a genuine provider observation
    with valid Bid/Ask, acceptable data status, and within age limits.
    """

    def __init__(
        self,
        cost_model: Optional[ExecutionCostModel] = None,
        max_fill_age_seconds: float = 120.0,
        max_spread_pct: float = 0.15,
        slippage_pct: float = 0.005,
        delayed_data_fill_allowed: bool = True,
        delayed_data_max_age_seconds: float = 300.0,
    ):
        self.cost_model = cost_model or ExecutionCostModel(slippage_pct=slippage_pct)
        self.max_fill_age_seconds = max_fill_age_seconds
        self.max_spread_pct = max_spread_pct
        self.slippage_pct = slippage_pct
        self.delayed_data_fill_allowed = delayed_data_fill_allowed
        self.delayed_data_max_age_seconds = delayed_data_max_age_seconds

        # Idempotency: track processed (order_id, observation_key) pairs
        self._processed_fills: Set[str] = set()

        # Ensure paper mode
        ExecutionGuard.assert_paper_mode()

    def _compute_fill_key(self, order_id: str, provider_timestamp: str, symbol: str) -> str:
        """Generate deterministic key for idempotent fill detection."""
        raw = f"{order_id}|{provider_timestamp}|{symbol}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def attempt_fill(
        self,
        order: PaperOrder,
        bid: Optional[float],
        ask: Optional[float],
        provider_timestamp: Optional[datetime],
        received_timestamp: Optional[datetime],
        data_status: str,
        source_provider: str,
        lot_size: int = 1,
    ) -> Tuple[Optional[PaperFill], Optional[ExecutionRefusal]]:
        """
        Attempt to execute a paper order against a genuine market observation.

        Returns:
            (PaperFill, None) if fill succeeds
            (None, ExecutionRefusal) if fill is refused

        NEVER returns a fill with fabricated prices.
        """
        now = datetime.now(timezone.utc)
        order_id = order.order_id

        # === EXECUTION ELIGIBILITY PIPELINE ===

        # 1. Paper mode check
        ExecutionGuard.validate_execution_mode("PAPER")

        # 2. Order status check
        if order.status not in (PaperOrderStatus.PENDING, PaperOrderStatus.OPEN):
            return None, ExecutionRefusal(
                order_id=order_id,
                reason="ORDER_NOT_ACTIVE",
                details=f"Order status is {order.status.value}",
            )

        # 3. Market hours check
        is_market_eligible, market_reason = is_fill_eligible_market_state()
        if not is_market_eligible:
            return None, ExecutionRefusal(
                order_id=order_id,
                reason="MARKET_CLOSED",
                details=market_reason,
                market_status=market_reason,
            )

        # 4. Data status check — STALE/UNAVAILABLE/ERROR = hard reject
        status_upper = data_status.upper().strip() if data_status else "UNAVAILABLE"
        if status_upper in _REJECT_STATUSES:
            return None, ExecutionRefusal(
                order_id=order_id,
                reason=f"{status_upper}_MARKET_DATA" if status_upper == "STALE" else f"{status_upper}_DATA",
                details=f"Data status '{status_upper}' is not eligible for paper execution",
                data_status=status_upper,
            )

        # 5. DELAYED data — check if policy allows and within age limit
        if status_upper == "DELAYED" and not self.delayed_data_fill_allowed:
            return None, ExecutionRefusal(
                order_id=order_id,
                reason="DELAYED_DATA_NOT_ALLOWED",
                details="Delayed data fills disabled by policy",
                data_status=status_upper,
            )

        # 6. Provider timestamp check
        if provider_timestamp is None:
            return None, ExecutionRefusal(
                order_id=order_id,
                reason="NO_PROVIDER_TIMESTAMP",
                details="Cannot determine quote age without provider timestamp",
            )

        if received_timestamp is None:
            received_timestamp = now

        # Timestamp relationship validation (provider <= received)
        if provider_timestamp > received_timestamp:
            time_diff = (provider_timestamp - received_timestamp).total_seconds()
            if time_diff > 5.0:  # Allow minimal clock skew
                return None, ExecutionRefusal(
                    order_id=order_id,
                    reason="INVALID_OBSERVATION_PROVENANCE",
                    details=f"Provider timestamp ({provider_timestamp.isoformat()}) is in future of received timestamp ({received_timestamp.isoformat()}) by {time_diff:.1f}s",
                )

        # 7. Retroactive fill check: observation must have been received after order submission
        if order.submitted_at is not None:
            if received_timestamp < order.submitted_at:
                return None, ExecutionRefusal(
                    order_id=order_id,
                    reason="RETROACTIVE_FILL_REJECTED",
                    details=f"Observation received at {received_timestamp.isoformat()} was prior to order submission at {order.submitted_at.isoformat()}",
                )

        # 8. Quote age check
        quote_age = (now - provider_timestamp).total_seconds()
        age_limit = (
            self.delayed_data_max_age_seconds
            if status_upper == "DELAYED"
            else self.max_fill_age_seconds
        )

        if quote_age > age_limit:
            return None, ExecutionRefusal(
                order_id=order_id,
                reason="QUOTE_TOO_OLD",
                details=f"Quote age {quote_age:.1f}s exceeds limit {age_limit:.1f}s",
                data_status=status_upper,
            )

        # 9. Bid/Ask presence — NEVER substitute LTP
        if order.side == PaperOrderSide.BUY:
            if ask is None or ask <= 0:
                return None, ExecutionRefusal(
                    order_id=order_id,
                    reason="NO_VALID_EXECUTABLE_QUOTE",
                    details="No valid Ask price available. LTP substitution is not allowed.",
                )
        elif order.side == PaperOrderSide.SELL:
            if bid is None or bid <= 0:
                return None, ExecutionRefusal(
                    order_id=order_id,
                    reason="NO_VALID_EXECUTABLE_QUOTE",
                    details="No valid Bid price available. LTP substitution is not allowed.",
                )

        # 9. Bid/Ask validity
        if bid is not None and ask is not None and bid > 0 and ask > 0:
            if bid > ask:
                return None, ExecutionRefusal(
                    order_id=order_id,
                    reason="INVALID_PRICE",
                    details=f"Crossed market: Bid {bid} > Ask {ask}",
                )

            # 10. Spread check
            midpoint = (bid + ask) / 2.0
            if midpoint > 0:
                spread_pct = (ask - bid) / midpoint
                if spread_pct > self.max_spread_pct:
                    return None, ExecutionRefusal(
                        order_id=order_id,
                        reason="SPREAD_TOO_WIDE",
                        details=f"Spread {spread_pct:.4f} ({spread_pct*100:.2f}%) exceeds limit {self.max_spread_pct:.4f} ({self.max_spread_pct*100:.2f}%)",
                    )

        # 11. Options data check
        if order.instrument_type in ("INDEX_OPTION", "STOCK_OPTION"):
            return None, ExecutionRefusal(
                order_id=order_id,
                reason="OPTIONS_DATA_UNAVAILABLE",
                details=(
                    "OPTIONS PAPER TRADING = UNAVAILABLE. "
                    "Options live readiness is NOT VERIFIED. "
                    "No synthetic option prices are used."
                ),
            )

        # 12. Order condition check (MARKET, LIMIT, STOP, STOP_LIMIT)
        fill_price, fill_source = self._evaluate_order_condition(
            order, bid, ask
        )
        if fill_price is None:
            return None, ExecutionRefusal(
                order_id=order_id,
                reason="ORDER_CONDITION_NOT_MET",
                details=f"Order condition not satisfied for {order.order_type.value} order",
            )

        # 13. Idempotency check
        fill_key = self._compute_fill_key(
            order_id, provider_timestamp.isoformat(), order.symbol
        )
        if fill_key in self._processed_fills:
            return None, ExecutionRefusal(
                order_id=order_id,
                reason="DUPLICATE_OBSERVATION",
                details="This observation has already been processed for this order",
            )

        # === FILL APPROVED ===

        # Apply slippage
        if order.side == PaperOrderSide.BUY:
            slippage_amount = fill_price * self.slippage_pct
            exec_price = round(fill_price + slippage_amount, 2)
        else:
            slippage_amount = fill_price * self.slippage_pct
            exec_price = round(fill_price - slippage_amount, 2)
            exec_price = max(0.05, exec_price)

        # Calculate transaction costs
        tx_costs = calculate_nse_option_transaction_costs(
            premium=exec_price,
            quantity=order.quantity,
            lots=max(1, order.quantity // max(1, lot_size)),
            action=order.side.value,
            cost_model=self.cost_model,
        )

        # Build fill with complete provenance
        spread_val = round(ask - bid, 4) if (bid is not None and ask is not None) else None
        fill = PaperFill(
            order_id=order_id,
            symbol=order.symbol,
            side=order.side,
            fill_quantity=order.quantity,
            fill_price=exec_price,
            fill_timestamp=now,
            provider=source_provider,
            source_provider=source_provider,
            provider_timestamp=provider_timestamp,
            received_timestamp=received_timestamp,
            order_submission_timestamp=order.submitted_at,
            decision_timestamp=order.decision_timestamp,
            execution_timestamp=now,
            bid_at_execution=bid,
            ask_at_execution=ask,
            spread_at_execution=spread_val,
            price_source=fill_source,
            price_source_description=f"{fill_source.value} from {source_provider} at {provider_timestamp.isoformat()}",
            data_status_at_fill=status_upper,
            slippage_applied=round(slippage_amount, 4),
            transaction_costs=round(tx_costs, 2),
            quote_age_seconds=round(quote_age, 2),
            execution_mode="PAPER",
        )

        # Validate provenance
        if not fill.validate_provenance():
            return None, ExecutionRefusal(
                order_id=order_id,
                reason="INSUFFICIENT_EXECUTION_PROVENANCE",
                details="Fill provenance validation failed",
            )

        # Mark as processed for idempotency
        self._processed_fills.add(fill_key)

        return fill, None

    def _evaluate_order_condition(
        self,
        order: PaperOrder,
        bid: Optional[float],
        ask: Optional[float],
    ) -> Tuple[Optional[float], Optional[PaperFillSource]]:
        """
        Evaluate whether the order condition is met.

        Returns (fill_price, fill_source) or (None, None).
        """
        if order.order_type == PaperOrderType.MARKET:
            if order.side == PaperOrderSide.BUY:
                return ask, PaperFillSource.PROVIDER_ASK_WITH_SLIPPAGE
            else:
                return bid, PaperFillSource.PROVIDER_BID_WITH_SLIPPAGE

        elif order.order_type == PaperOrderType.LIMIT:
            if order.limit_price is None:
                return None, None

            if order.side == PaperOrderSide.BUY:
                # BUY limit: fill if current ask <= limit_price
                if ask is not None and ask > 0 and ask <= order.limit_price:
                    return ask, PaperFillSource.PROVIDER_ASK_WITH_SLIPPAGE
            else:
                # SELL limit: fill if current bid >= limit_price
                if bid is not None and bid > 0 and bid >= order.limit_price:
                    return bid, PaperFillSource.PROVIDER_BID_WITH_SLIPPAGE

            return None, None

        elif order.order_type == PaperOrderType.STOP:
            if order.stop_price is None:
                return None, None

            # Check if stop is triggered
            if order.side == PaperOrderSide.BUY:
                # BUY stop: triggers when ask >= stop_price
                if ask is not None and ask > 0 and ask >= order.stop_price:
                    return ask, PaperFillSource.PROVIDER_ASK_WITH_SLIPPAGE
            else:
                # SELL stop: triggers when bid <= stop_price
                if bid is not None and bid > 0 and bid <= order.stop_price:
                    return bid, PaperFillSource.PROVIDER_BID_WITH_SLIPPAGE

            return None, None

        elif order.order_type == PaperOrderType.STOP_LIMIT:
            if order.stop_price is None or order.limit_price is None:
                return None, None

            # First check stop trigger, then limit condition
            if order.side == PaperOrderSide.BUY:
                if ask is not None and ask > 0:
                    if ask >= order.stop_price and ask <= order.limit_price:
                        return ask, PaperFillSource.PROVIDER_ASK_WITH_SLIPPAGE
            else:
                if bid is not None and bid > 0:
                    if bid <= order.stop_price and bid >= order.limit_price:
                        return bid, PaperFillSource.PROVIDER_BID_WITH_SLIPPAGE

            return None, None

        return None, None

    def reset_idempotency_cache(self) -> None:
        """Clear the processed fills cache (for session reset)."""
        self._processed_fills.clear()
