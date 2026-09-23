"""
Pydantic schemas and dataclasses for the Options Backtesting Engine.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from src.ingestion.schemas import OptionType
from src.options.portfolio_greeks import PortfolioGreeks
from src.strategies.templates import StrategyLegDetail


class LiquidityMode(str, Enum):
    STRICT = "STRICT"
    NORMAL = "NORMAL"
    RELAXED = "RELAXED"


class CostModelType(str, Enum):
    ZERO_COST = "ZERO_COST"
    BASE = "BASE"
    CONSERVATIVE = "CONSERVATIVE"
    HIGH_COST = "HIGH_COST"


class ExecutionCostModel(BaseModel):
    model_type: CostModelType = CostModelType.BASE
    slippage_pct: float = 0.005          # 0.5% price slippage default
    brokerage_per_lot: float = 20.0       # INR 20 per lot
    stt_rate_pct: float = 0.000625        # 0.0625% STT on sell option premium
    exchange_fee_pct: float = 0.00053     # NSE transaction charge (0.053%)
    gst_rate_pct: float = 0.18            # 18% GST on brokerage + exchange fee
    sebi_fee_pct: float = 0.000001        # SEBI turnover charge
    stamp_duty_rate_pct: float = 0.00003  # 0.003% Stamp duty on BUY side only (Phase 17 fix)


class BacktestConfig(BaseModel):
    symbol: str = "NIFTY"
    start_date: date = Field(default_factory=lambda: date(2026, 1, 1))
    end_date: date = Field(default_factory=lambda: date(2026, 2, 1))
    initial_equity: float = 1_000_000.0   # INR 10 Lakhs
    max_risk_pct_per_trade: float = 0.02 # 2% max risk per trade
    max_open_positions: int = 3
    strategy_name: str = "Bull Call Spread"
    min_strategy_score: float = 60.0
    stop_loss_pct: Optional[float] = 0.50 # 50% max loss stop loss
    take_profit_pct: Optional[float] = 1.00 # 100% max profit target
    exit_dte_threshold: int = 2          # Exit 2 days prior to expiry
    liquidity_mode: LiquidityMode = LiquidityMode.NORMAL
    cost_model: ExecutionCostModel = Field(default_factory=ExecutionCostModel)
    use_synthetic_if_unavailable: bool = True  # Allows test execution with synthetic data fixtures


class TradeLegExecution(BaseModel):
    contract_symbol: str
    option_type: OptionType
    strike_price: float
    expiry_date: date
    action: str                        # BUY or SELL
    quantity: int                      # Total contracts (lots * lot_size)
    lots: int
    entry_timestamp: datetime
    entry_bid: float
    entry_ask: float
    entry_exec_price: float            # Slippage-adjusted price
    entry_costs: float                 # Fees & taxes on entry
    
    exit_timestamp: Optional[datetime] = None
    exit_bid: Optional[float] = None
    exit_ask: Optional[float] = None
    exit_exec_price: Optional[float] = None
    exit_costs: float = 0.0            # Fees & taxes on exit
    leg_pnl: float = 0.0               # Net leg P/L after costs


class SimulatedPosition(BaseModel):
    trade_id: str
    strategy_name: str
    symbol: str
    entry_timestamp: datetime
    legs: List[TradeLegExecution]
    quantity: int                      # Lots
    initial_capital_required: float
    max_loss: float
    max_profit: float
    breakevens: List[float]
    net_greeks_at_entry: PortfolioGreeks
    entry_underlying_price: float
    entry_score: float
    
    # State tracking
    is_open: bool = True
    highest_pnl: float = 0.0
    lowest_pnl: float = 0.0
    current_pnl: float = 0.0


class ExecutedTrade(BaseModel):
    trade_id: str
    strategy_name: str
    symbol: str
    entry_timestamp: datetime
    exit_timestamp: datetime
    entry_underlying_price: float
    exit_underlying_price: float
    legs: List[TradeLegExecution]
    lots: int
    gross_pnl: float
    total_costs: float
    net_pnl: float
    return_pct_on_risk: float
    exit_reason: str                   # STOP_LOSS, PROFIT_TARGET, EXPIRY, DTE_EXIT, SIGNAL_EXIT
    max_adverse_excursion: float       # MAE (worst unrealized P/L during trade)
    max_favorable_excursion: float     # MFE (best unrealized P/L during trade)
    holding_days: float
    regime_at_entry: str = "NEUTRAL"
    vol_regime_at_entry: str = "NORMAL"
    is_synthetic: bool = False


class PortfolioSnapshot(BaseModel):
    timestamp: datetime
    cash_balance: float
    equity: float
    unrealized_pnl: float
    realized_pnl_cum: float
    open_positions_count: int
    net_delta: float = 0.0
    net_gamma: float = 0.0
    net_theta: float = 0.0
    net_vega: float = 0.0
    drawdown_pct: float = 0.0


class PerformanceMetrics(BaseModel):
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    gross_pnl: float = 0.0
    total_costs: float = 0.0
    net_pnl: float = 0.0
    total_return_pct: float = 0.0
    cagr_pct: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    expectancy: float = 0.0
    profit_factor: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    avg_holding_days: float = 0.0
    max_adverse_excursion_avg: float = 0.0
    max_favorable_excursion_avg: float = 0.0
    sample_size_sufficient: bool = False


class BacktestResult(BaseModel):
    config: BacktestConfig
    data_source: str
    data_quality_label: str
    critical_labels: List[str]         # e.g. ["OUT-OF-SAMPLE", "SYNTHETIC TEST DATA — SOFTWARE TESTING ONLY"]
    metrics: PerformanceMetrics
    trades: List[ExecutedTrade] = Field(default_factory=list)
    equity_curve: List[PortfolioSnapshot] = Field(default_factory=list)
    regime_performance: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    baseline_underlying_return_pct: float = 0.0
    parameter_robustness_status: str = "NOT_EVALUATED" # STABLE, FRAGILE / POSSIBLE OVERFITTING
    execution_time_sec: float = 0.0
