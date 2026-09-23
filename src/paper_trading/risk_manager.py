"""
Phase 8 — Paper Risk Manager.

Every order MUST pass through risk checks before execution.
All limits are CONFIGURED PAPER RISK LIMITS, not universally safe recommendations.
Circuit breakers cancel pending orders and reject new orders when triggered.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.paper_trading.models import (
    PaperOrder,
    PaperOrderSide,
    PaperOrderStatus,
    PaperPosition,
    RiskCheckResult,
)


class PaperRiskManager:
    """
    Pre-trade risk manager for paper trading.

    All limits are CONFIGURED PAPER RISK LIMITS.
    They are configurable simulation controls, NOT universally safe recommendations.
    """

    def __init__(
        self,
        max_position_size_lots: int = 50,
        max_open_positions: int = 5,
        max_risk_per_trade_pct: float = 2.0,
        max_daily_loss_pct: float = 5.0,
        max_portfolio_drawdown_pct: float = 15.0,
        max_total_exposure: Optional[float] = None,
        lot_size: int = 25,
    ):
        self.max_position_size_lots = max_position_size_lots
        self.max_open_positions = max_open_positions
        self.max_risk_per_trade_pct = max_risk_per_trade_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_portfolio_drawdown_pct = max_portfolio_drawdown_pct
        self.max_total_exposure = max_total_exposure
        self.lot_size = lot_size

        # Circuit breaker state
        self._daily_loss_breaker_active: bool = False
        self._drawdown_breaker_active: bool = False
        self._risk_events: List[Dict[str, Any]] = []

    def check_order(
        self,
        order: PaperOrder,
        current_equity: float,
        daily_pnl: float,
        drawdown_pct: float,
        open_positions: List[PaperPosition],
        total_exposure: float = 0.0,
    ) -> RiskCheckResult:
        """
        Comprehensive pre-trade risk check.

        Every order MUST pass this before execution.
        """
        rejection_reasons: List[str] = []
        now = datetime.now(timezone.utc)

        # 1. Circuit breaker check
        if self._daily_loss_breaker_active:
            rejection_reasons.append("CIRCUIT_BREAKER: Daily loss limit breached. New orders rejected.")

        if self._drawdown_breaker_active:
            rejection_reasons.append("CIRCUIT_BREAKER: Portfolio drawdown limit breached. New orders rejected.")

        # 2. Position size limit
        lots = order.quantity // max(1, self.lot_size)
        if lots > self.max_position_size_lots:
            rejection_reasons.append(
                f"POSITION_SIZE: {lots} lots exceeds CONFIGURED PAPER RISK LIMIT of {self.max_position_size_lots} lots."
            )

        # 3. Open positions limit
        open_count = len([p for p in open_positions if p.is_open])
        if open_count >= self.max_open_positions:
            rejection_reasons.append(
                f"OPEN_POSITIONS: {open_count} open positions reaches CONFIGURED PAPER RISK LIMIT of {self.max_open_positions}."
            )

        # 4. Per-trade risk limit
        if current_equity > 0:
            # Estimate risk as full premium for simplicity
            estimated_risk = order.quantity * (order.limit_price or 0)
            if estimated_risk == 0:
                estimated_risk = current_equity * 0.01  # Conservative 1% estimate
            risk_pct = (estimated_risk / current_equity) * 100.0
            if risk_pct > self.max_risk_per_trade_pct:
                rejection_reasons.append(
                    f"TRADE_RISK: Estimated risk {risk_pct:.2f}% exceeds CONFIGURED PAPER RISK LIMIT of {self.max_risk_per_trade_pct}%."
                )

        # 5. Daily loss check
        if current_equity > 0:
            daily_loss_pct = abs(min(0, daily_pnl)) / current_equity * 100.0
            if daily_loss_pct >= self.max_daily_loss_pct:
                rejection_reasons.append(
                    f"DAILY_LOSS: Daily loss {daily_loss_pct:.2f}% meets/exceeds CONFIGURED PAPER RISK LIMIT of {self.max_daily_loss_pct}%."
                )

        # 6. Portfolio drawdown check
        if drawdown_pct * 100 >= self.max_portfolio_drawdown_pct:
            rejection_reasons.append(
                f"DRAWDOWN: Portfolio drawdown {drawdown_pct*100:.2f}% meets/exceeds CONFIGURED PAPER RISK LIMIT of {self.max_portfolio_drawdown_pct}%."
            )

        # 7. Total exposure check
        if self.max_total_exposure is not None and total_exposure > self.max_total_exposure:
            rejection_reasons.append(
                f"TOTAL_EXPOSURE: Exposure ₹{total_exposure:,.0f} exceeds CONFIGURED PAPER RISK LIMIT of ₹{self.max_total_exposure:,.0f}."
            )

        # 8. Options availability check
        if order.instrument_type in ("INDEX_OPTION", "STOCK_OPTION"):
            rejection_reasons.append(
                "OPTIONS_DATA_UNAVAILABLE: Options live readiness is NOT VERIFIED. "
                "Options paper trading is UNAVAILABLE."
            )

        is_approved = len(rejection_reasons) == 0

        risk_metrics = {
            "current_equity": current_equity,
            "daily_pnl": daily_pnl,
            "drawdown_pct": drawdown_pct,
            "open_positions_count": open_count,
            "total_exposure": total_exposure,
            "circuit_breaker_daily_loss": self._daily_loss_breaker_active,
            "circuit_breaker_drawdown": self._drawdown_breaker_active,
        }

        return RiskCheckResult(
            is_approved=is_approved,
            rejection_reasons=rejection_reasons,
            risk_metrics=risk_metrics,
            timestamp=now,
        )

    def update_circuit_breakers(
        self,
        daily_pnl: float,
        current_equity: float,
        drawdown_pct: float,
    ) -> List[str]:
        """
        Check and potentially trigger circuit breakers.

        Returns list of triggered breaker names.
        """
        triggered = []

        # Daily loss circuit breaker
        if current_equity > 0:
            daily_loss_pct = abs(min(0, daily_pnl)) / current_equity * 100.0
            if daily_loss_pct >= self.max_daily_loss_pct and not self._daily_loss_breaker_active:
                self._daily_loss_breaker_active = True
                event = {
                    "type": "DAILY_LOSS_CIRCUIT_BREAKER",
                    "triggered_at": datetime.now(timezone.utc).isoformat(),
                    "daily_loss_pct": daily_loss_pct,
                    "threshold": self.max_daily_loss_pct,
                }
                self._risk_events.append(event)
                triggered.append("DAILY_LOSS_CIRCUIT_BREAKER")

        # Portfolio drawdown circuit breaker
        if drawdown_pct * 100 >= self.max_portfolio_drawdown_pct and not self._drawdown_breaker_active:
            self._drawdown_breaker_active = True
            event = {
                "type": "DRAWDOWN_CIRCUIT_BREAKER",
                "triggered_at": datetime.now(timezone.utc).isoformat(),
                "drawdown_pct": drawdown_pct * 100,
                "threshold": self.max_portfolio_drawdown_pct,
            }
            self._risk_events.append(event)
            triggered.append("DRAWDOWN_CIRCUIT_BREAKER")

        return triggered

    def reset_circuit_breakers(self) -> None:
        """Manual reset of circuit breakers."""
        self._daily_loss_breaker_active = False
        self._drawdown_breaker_active = False
        self._risk_events.append({
            "type": "CIRCUIT_BREAKER_RESET",
            "reset_at": datetime.now(timezone.utc).isoformat(),
            "method": "MANUAL_RESET",
        })

    def reset_daily_circuit_breaker(self) -> None:
        """Reset daily loss circuit breaker for new trading day."""
        if self._daily_loss_breaker_active:
            self._daily_loss_breaker_active = False
            self._risk_events.append({
                "type": "DAILY_LOSS_BREAKER_RESET",
                "reset_at": datetime.now(timezone.utc).isoformat(),
                "method": "NEXT_TRADING_DAY",
            })

    @property
    def is_circuit_breaker_active(self) -> bool:
        return self._daily_loss_breaker_active or self._drawdown_breaker_active

    def get_risk_events(self) -> List[Dict]:
        return list(self._risk_events)

    def get_risk_status(self) -> Dict[str, Any]:
        return {
            "daily_loss_circuit_breaker": self._daily_loss_breaker_active,
            "drawdown_circuit_breaker": self._drawdown_breaker_active,
            "is_any_breaker_active": self.is_circuit_breaker_active,
            "configured_limits": {
                "max_position_size_lots": self.max_position_size_lots,
                "max_open_positions": self.max_open_positions,
                "max_risk_per_trade_pct": self.max_risk_per_trade_pct,
                "max_daily_loss_pct": self.max_daily_loss_pct,
                "max_portfolio_drawdown_pct": self.max_portfolio_drawdown_pct,
                "label": "CONFIGURED PAPER RISK LIMITS",
            },
            "risk_events_count": len(self._risk_events),
        }
