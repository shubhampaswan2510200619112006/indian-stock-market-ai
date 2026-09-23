"""
Phase 9.6 — Research Question J: Cost Decomposition & Edge Destruction Engine.

Decomposes trading strategy P&L into exact components:
Gross Alpha - Statutory Fees (STT, NSE, GST, Stamp) - Execution Slippage = Net Alpha.

Explicitly categorizes results into the 3 mandated failure modes:
- Case A: No Gross Edge (Strategy fails before any transaction costs are applied).
- Case B: Weak Gross Edge Destroyed by Costs (Gross P&L is positive, but transaction drag flips it negative).
- Case C: Meaningful Gross Edge Survives Costs (Strategy achieves positive net alpha after realistic friction).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.ml.economic_metrics import EconomicMetricsEngine, IndianMarketFrictionModel


class CostFailureMode(str, Enum):
    CASE_A_NO_GROSS_EDGE = "CASE_A_NO_GROSS_EDGE"
    CASE_B_COST_DESTROYED_EDGE = "CASE_B_COST_DESTROYED_EDGE"
    CASE_C_SURVIVING_EDGE = "CASE_C_SURVIVING_EDGE"


@dataclass
class CostDecompositionReport:
    gross_pnl_pct: float
    statutory_fees_pct: float
    slippage_pct: float
    total_frictions_pct: float
    net_pnl_pct: float
    friction_to_gross_ratio: float
    failure_mode: CostFailureMode
    diagnosis: str


class CostAnalysisEngine:
    """
    Decomposes P&L into gross alpha, statutory fees, and slippage.
    """

    @classmethod
    def decompose_costs(
        cls,
        signals: np.ndarray,
        asset_returns: np.ndarray,
        base_fee_pct: float = 0.0005,
        base_slippage_pct: float = 0.0005,
    ) -> CostDecompositionReport:
        n = min(len(signals), len(asset_returns))
        sigs = signals[:n]
        rets = asset_returns[:n]

        # Zero friction simulation (Gross)
        zero_friction = IndianMarketFrictionModel(base_fee_pct=0.0, base_slippage_pct=0.0)
        gross_econ = EconomicMetricsEngine.evaluate_strategy_returns(sigs, rets, zero_friction)

        # Realistic friction simulation (Net)
        real_friction = IndianMarketFrictionModel(base_fee_pct=base_fee_pct, base_slippage_pct=base_slippage_pct)
        net_econ = EconomicMetricsEngine.evaluate_strategy_returns(sigs, rets, real_friction)

        gross_ret = gross_econ.gross_return
        fees = net_econ.total_fees
        slip = net_econ.total_slippage
        total_fric = fees + slip
        net_ret = net_econ.net_return

        ratio = (total_fric / gross_ret) if abs(gross_ret) > 1e-6 else 999.0

        if gross_ret <= 0.0:
            mode = CostFailureMode.CASE_A_NO_GROSS_EDGE
            diag = (
                f"CASE A — NO GROSS EDGE: Strategy generated negative gross return ({gross_ret:+.2%}) "
                "before any transaction costs or slippage were deducted. The underlying predictive signal is uninformative."
            )
        elif gross_ret > 0.0 and net_ret <= 0.0:
            mode = CostFailureMode.CASE_B_COST_DESTROYED_EDGE
            diag = (
                f"CASE B — WEAK GROSS EDGE DESTROYED BY COSTS: Strategy achieved positive gross return ({gross_ret:+.2%}), "
                f"but transaction friction ({total_fric:.2%}) exceeded gross alpha, turning net return negative ({net_ret:+.2%})."
            )
        else:
            mode = CostFailureMode.CASE_C_SURVIVING_EDGE
            diag = (
                f"CASE C — SURVIVING GROSS EDGE: Strategy achieved positive gross return ({gross_ret:+.2%}) "
                f"that exceeded realistic transaction friction ({total_fric:.2%}), yielding positive net return ({net_ret:+.2%})."
            )

        return CostDecompositionReport(
            gross_pnl_pct=gross_ret,
            statutory_fees_pct=fees,
            slippage_pct=slip,
            total_frictions_pct=total_fric,
            net_pnl_pct=net_ret,
            friction_to_gross_ratio=ratio,
            failure_mode=mode,
            diagnosis=diag,
        )
