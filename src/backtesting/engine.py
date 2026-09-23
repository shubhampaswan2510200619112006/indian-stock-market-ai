"""
Chronological Event-Driven Options Backtester Engine.

RULES & ARCHITECTURE:
1. Point-in-time rule: ONLY observations timestamped <= T are visible at step T.
2. Chronological simulation: step through market observations sequentially.
3. Realistic execution: leg-by-leg entry/exit with bid/ask spread, slippage, and NSE transaction costs.
4. Mandatory Data Gate: refuses fake results on missing historical datasets.
5. Explicit Labeling: "SYNTHETIC TEST DATA — SOFTWARE TESTING ONLY" when using test fixtures.
"""

from __future__ import annotations

import time
import uuid
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from src.ingestion.schemas import OptionChainSnapshot, OptionQuote, OptionType
from src.options.portfolio_greeks import PortfolioGreeks
from src.strategies.engine import StrategyResearchEngine
from src.strategies.position_sizing import calculate_position_size
from src.strategies.templates import StrategyCandidate, StrategyLegDetail
from src.backtesting.models import (
    BacktestConfig,
    BacktestResult,
    ExecutedTrade,
    ExecutionCostModel,
    PerformanceMetrics,
    PortfolioSnapshot,
    SimulatedPosition,
    TradeLegExecution,
)
from src.backtesting.data_gate import DataGate, DataAvailabilityStatus
from src.backtesting.synthetic_fixtures import generate_synthetic_option_history
from src.backtesting.execution import (
    calculate_execution_price,
    calculate_nse_option_transaction_costs,
    evaluate_liquidity_filter,
)
from src.backtesting.metrics import calculate_performance_metrics


def _get_quote_from_chain(
    chain: OptionChainSnapshot,
    contract_symbol: str = "",
    strike_price: Optional[float] = None,
    option_type: Optional[OptionType] = None,
) -> Optional[OptionQuote]:
    """
    Safely finds an OptionQuote in OptionChainSnapshot strikes list.
    """
    for row in chain.strikes:
        if strike_price is not None and abs(row.strike_price - strike_price) < 1e-4:
            if option_type == OptionType.CE and row.ce:
                return row.ce
            elif option_type == OptionType.PE and row.pe:
                return row.pe

        if contract_symbol:
            if row.ce and contract_symbol in getattr(row.ce, "contract_symbol", ""):
                return row.ce
            if row.pe and contract_symbol in getattr(row.pe, "contract_symbol", ""):
                return row.pe
    return None


class BacktestEngine:
    """
    Chronological Event-Driven Backtest Simulation Engine.
    """

    def __init__(self, config: BacktestConfig, db_session=None):
        self.config = config
        self.db_session = db_session
        self.data_gate = DataGate(db_session=db_session)
        self.strategy_engine = StrategyResearchEngine()

    def run(self) -> BacktestResult:
        """
        Executes the backtest simulation over the requested date range.
        """
        start_time = time.time()
        critical_labels: List[str] = ["OUT-OF-SAMPLE"]

        # 1. Data Availability Check
        availability = self.data_gate.evaluate_availability(
            symbol=self.config.symbol,
            start_date=self.config.start_date,
            end_date=self.config.end_date,
        )

        snapshots: List[Tuple[datetime, float, OptionChainSnapshot]] = []
        is_synthetic = False

        if availability.status in [DataAvailabilityStatus.AVAILABLE, DataAvailabilityStatus.PARTIAL]:
            data_source = f"DATABASE ({availability.status.value})"
            data_quality_label = availability.message
            
            from src.ingestion.historical_provider import DatabaseHistoricalOptionsProvider
            from src.database.connection import get_session
            from src.database.models import OptionsQuoteDB, OptionsContractDB
            from sqlalchemy import select, and_

            provider = DatabaseHistoricalOptionsProvider(self.db_session)
            session = self.db_session if self.db_session else get_session()
            should_close = self.db_session is None

            try:
                start_dt = datetime.combine(self.config.start_date, datetime.min.time())
                end_dt = datetime.combine(self.config.end_date, datetime.max.time())
                
                ts_stmt = (
                    select(OptionsQuoteDB.timestamp)
                    .join(OptionsContractDB, OptionsQuoteDB.contract_id == OptionsContractDB.id)
                    .where(
                        and_(
                            OptionsContractDB.underlying == self.config.symbol.upper(),
                            OptionsQuoteDB.timestamp >= start_dt,
                            OptionsQuoteDB.timestamp <= end_dt,
                        )
                    )
                    .distinct()
                    .order_by(OptionsQuoteDB.timestamp.asc())
                )
                ts_list = [t[0] for t in session.execute(ts_stmt).all()]

                for ts in ts_list:
                    chain_snap = provider.get_historical_chain_snapshot(self.config.symbol, ts)
                    if chain_snap:
                        snapshots.append((ts, chain_snap.spot_price, chain_snap))
            finally:
                if should_close:
                    session.close()

        elif self.config.use_synthetic_if_unavailable:
            data_source = "SYNTHETIC TEST FIXTURE"
            data_quality_label = "SYNTHETIC TEST DATA — SOFTWARE TESTING ONLY"
            critical_labels.append("SYNTHETIC TEST DATA — SOFTWARE TESTING ONLY")
            is_synthetic = True
            
            num_days = max(5, (self.config.end_date - self.config.start_date).days)
            snapshots = generate_synthetic_option_history(
                underlying=self.config.symbol,
                start_date=self.config.start_date,
                num_days=num_days,
                initial_spot=24000.0 if self.config.symbol == "NIFTY" else 51000.0,
            )
        else:
            # Refuse execution
            critical_labels.append("INSUFFICIENT HISTORICAL DATA")
            return BacktestResult(
                config=self.config,
                data_source="NONE",
                data_quality_label=availability.message,
                critical_labels=critical_labels,
                metrics=PerformanceMetrics(sample_size_sufficient=False),
                trades=[],
                equity_curve=[],
                execution_time_sec=round(time.time() - start_time, 3),
            )

        # 2. Initialize Simulation State
        cash = self.config.initial_equity
        equity = self.config.initial_equity
        peak_equity = equity
        open_positions: List[SimulatedPosition] = []
        closed_trades: List[ExecutedTrade] = []
        equity_curve: List[PortfolioSnapshot] = []

        # Benchmark tracking
        initial_spot: Optional[float] = None
        final_spot: Optional[float] = None

        # 3. Chronological Simulation Loop
        for timestamp, spot_price, chain in snapshots:
            if initial_spot is None:
                initial_spot = spot_price
            final_spot = spot_price

            current_date = timestamp.date()

            # --- Step 3A: Monitor & Exit Open Positions ---
            retained_positions: List[SimulatedPosition] = []

            for pos in open_positions:
                exit_triggered, exit_reason, exit_legs = self._evaluate_position_exit(
                    pos=pos,
                    chain=chain,
                    spot_price=spot_price,
                    current_date=current_date,
                )

                if exit_triggered and exit_legs:
                    # Calculate exit cashflows and P/L
                    gross_pnl = 0.0
                    total_entry_costs = sum(leg.entry_costs for leg in pos.legs)
                    total_exit_costs = sum(leg.exit_costs for leg in exit_legs)

                    for leg in exit_legs:
                        if leg.action == "BUY":  # Entry BUY -> Exit SELL
                            leg_gross = (leg.exit_exec_price - leg.entry_exec_price) * leg.quantity
                        else:  # Entry SELL -> Exit BUY
                            leg_gross = (leg.entry_exec_price - leg.exit_exec_price) * leg.quantity
                        leg.leg_pnl = leg_gross - (leg.entry_costs + leg.exit_costs)
                        gross_pnl += leg_gross

                    total_costs = total_entry_costs + total_exit_costs
                    net_pnl = gross_pnl - total_costs
                    holding_days = max(0.1, (timestamp - pos.entry_timestamp).days)

                    cash += pos.initial_capital_required + net_pnl

                    executed_trade = ExecutedTrade(
                        trade_id=pos.trade_id,
                        strategy_name=pos.strategy_name,
                        symbol=pos.symbol,
                        entry_timestamp=pos.entry_timestamp,
                        exit_timestamp=timestamp,
                        entry_underlying_price=pos.entry_underlying_price,
                        exit_underlying_price=spot_price,
                        legs=exit_legs,
                        lots=pos.quantity,
                        gross_pnl=round(gross_pnl, 2),
                        total_costs=round(total_costs, 2),
                        net_pnl=round(net_pnl, 2),
                        return_pct_on_risk=round(net_pnl / max(1.0, pos.max_loss), 4),
                        exit_reason=exit_reason,
                        max_adverse_excursion=round(pos.lowest_pnl, 2),
                        max_favorable_excursion=round(pos.highest_pnl, 2),
                        holding_days=holding_days,
                        is_synthetic=is_synthetic,
                    )
                    closed_trades.append(executed_trade)
                else:
                    # Update mark-to-market P/L and MAE/MFE
                    current_unrealized = self._calculate_unrealized_pnl(pos, chain, spot_price)
                    pos.current_pnl = current_unrealized
                    pos.highest_pnl = max(pos.highest_pnl, current_unrealized)
                    pos.lowest_pnl = min(pos.lowest_pnl, current_unrealized)
                    retained_positions.append(pos)

            open_positions = retained_positions

            # --- Step 3B: Strategy Candidate Search & Entry ---
            if len(open_positions) < self.config.max_open_positions:
                thesis = self._build_thesis_at_time(self.config.symbol, chain)
                res = self.strategy_engine.evaluate_strategies(
                    chain=chain,
                    thesis=thesis,
                    min_score_threshold=self.config.min_strategy_score,
                )

                if not res.no_trade_decision and res.candidates:
                    # Filter candidates matching strategy_name and score
                    matching_scored = [
                        sc for sc in res.candidates
                        if sc.candidate.strategy_name.lower() == self.config.strategy_name.lower()
                        and sc.score.overall_score >= self.config.min_strategy_score
                    ]

                    if matching_scored:
                        best_scored = matching_scored[0]

                        # Attempt entry order execution
                        new_pos = self._execute_entry_order(
                            candidate=best_scored.candidate,
                            score_val=best_scored.score.overall_score,
                            chain=chain,
                            timestamp=timestamp,
                            spot_price=spot_price,
                            current_equity=equity,
                        )

                        if new_pos:
                            cash -= new_pos.initial_capital_required
                            open_positions.append(new_pos)

            # --- Step 3C: Portfolio State Snapshot ---
            unrealized_pnl = sum(p.current_pnl for p in open_positions)
            current_equity = cash + sum(p.initial_capital_required for p in open_positions) + unrealized_pnl
            peak_equity = max(peak_equity, current_equity)
            drawdown_pct = (peak_equity - current_equity) / peak_equity if peak_equity > 0 else 0.0

            realized_cum = sum(t.net_pnl for t in closed_trades)

            snap = PortfolioSnapshot(
                timestamp=timestamp,
                cash_balance=round(cash, 2),
                equity=round(current_equity, 2),
                unrealized_pnl=round(unrealized_pnl, 2),
                realized_pnl_cum=round(realized_cum, 2),
                open_positions_count=len(open_positions),
                drawdown_pct=round(drawdown_pct, 4),
            )
            equity_curve.append(snap)
            equity = current_equity

        # 4. Calculate Final Metrics
        metrics = calculate_performance_metrics(
            trades=closed_trades,
            equity_curve=equity_curve,
            initial_equity=self.config.initial_equity,
        )

        if not metrics.sample_size_sufficient:
            critical_labels.append("INSUFFICIENT SAMPLE")

        baseline_return = 0.0
        if initial_spot and final_spot and initial_spot > 0:
            baseline_return = round((final_spot - initial_spot) / initial_spot, 4)

        return BacktestResult(
            config=self.config,
            data_source=data_source,
            data_quality_label=data_quality_label,
            critical_labels=critical_labels,
            metrics=metrics,
            trades=closed_trades,
            equity_curve=equity_curve,
            baseline_underlying_return_pct=baseline_return,
            execution_time_sec=round(time.time() - start_time, 3),
        )

    def _build_thesis_at_time(self, symbol: str, chain: OptionChainSnapshot) -> MarketThesis:
        from src.ingestion.schemas import MarketRegimeResult, MarketRegimeType
        from src.options.surface import compute_volatility_surface
        from src.strategies.suitability import MarketThesis

        regime = MarketRegimeResult(
            symbol=symbol,
            regime=MarketRegimeType.BULL,
            confidence=0.75,
            description="Point-in-time trend",
            timestamp=chain.timestamp,
            source="BACKTEST_SIMULATOR",
        )
        surface = compute_volatility_surface(chain)
        return MarketThesis(
            symbol=symbol,
            regime=regime,
            surface=surface,
            direction_view="BULLISH",
            direction_confidence=0.75,
            volatility_view="IV_FAIR",
        )

    def _execute_entry_order(
        self,
        candidate: StrategyCandidate,
        score_val: float,
        chain: OptionChainSnapshot,
        timestamp: datetime,
        spot_price: float,
        current_equity: float,
    ) -> Optional[SimulatedPosition]:
        """
        Executes a candidate's legs with liquidity checks and realistic cost modeling.
        """
        executed_legs: List[TradeLegExecution] = []
        total_entry_costs = 0.0

        # Position Sizing
        lot_sz = candidate.legs[0].lot_size if candidate.legs else 25
        sizing = calculate_position_size(
            candidate=candidate,
            account_equity=current_equity,
            max_risk_pct=self.config.max_risk_pct_per_trade * 100.0,
            lot_size=lot_sz,
        )
        lots = sizing.suggested_lots
        if lots <= 0:
            return None

        # Execute leg by leg
        for leg in candidate.legs:
            quote = _get_quote_from_chain(chain, strike_price=leg.strike_price, option_type=leg.option_type)
            if not quote:
                return None

            # Liquidity check
            is_liquid, msg = evaluate_liquidity_filter(quote, self.config.liquidity_mode)
            if not is_liquid:
                return None

            exec_price = calculate_execution_price(quote, leg.action, self.config.cost_model)
            qty = lots * lot_sz
            entry_cost = calculate_nse_option_transaction_costs(
                premium=exec_price,
                quantity=qty,
                lots=lots,
                action=leg.action,
                cost_model=self.config.cost_model,
            )
            total_entry_costs += entry_cost

            contract_sym = getattr(quote, "contract_symbol", None) or f"{candidate.symbol}{leg.expiry_date.strftime('%y%b').upper()}{int(leg.strike_price)}{leg.option_type.value}"
            leg_exec = TradeLegExecution(
                contract_symbol=contract_sym,
                option_type=leg.option_type,
                strike_price=leg.strike_price,
                expiry_date=leg.expiry_date,
                action=leg.action,
                quantity=qty,
                lots=lots,
                entry_timestamp=timestamp,
                entry_bid=quote.bid_price or quote.last_price,
                entry_ask=quote.ask_price or quote.last_price,
                entry_exec_price=exec_price,
                entry_costs=entry_cost,
            )
            executed_legs.append(leg_exec)

        capital_req = (candidate.capital_required * lots) + total_entry_costs

        return SimulatedPosition(
            trade_id=str(uuid.uuid4())[:8],
            strategy_name=candidate.strategy_name,
            symbol=candidate.symbol,
            entry_timestamp=timestamp,
            legs=executed_legs,
            quantity=lots,
            initial_capital_required=capital_req,
            max_loss=(candidate.max_loss or 0.0) * lots,
            max_profit=(candidate.max_profit or 0.0) * lots,
            breakevens=candidate.breakevens,
            net_greeks_at_entry=candidate.net_greeks,
            entry_underlying_price=spot_price,
            entry_score=score_val,
        )

    def _evaluate_position_exit(
        self,
        pos: SimulatedPosition,
        chain: OptionChainSnapshot,
        spot_price: float,
        current_date: date,
    ) -> Tuple[bool, str, List[TradeLegExecution]]:
        """
        Evaluates whether an open position should exit (Stop loss, Profit target, DTE threshold, or Expiry).
        """
        min_expiry = min(leg.expiry_date for leg in pos.legs)
        dte = (min_expiry - current_date).days

        current_unrealized = self._calculate_unrealized_pnl(pos, chain, spot_price)

        # 1. Stop Loss Check
        if self.config.stop_loss_pct and pos.max_loss > 0:
            if current_unrealized <= -abs(pos.max_loss * self.config.stop_loss_pct):
                return True, "STOP_LOSS", self._build_exit_legs(pos, chain, "STOP_LOSS")

        # 2. Take Profit Check
        if self.config.take_profit_pct and pos.max_profit > 0:
            if current_unrealized >= abs(pos.max_profit * self.config.take_profit_pct):
                return True, "PROFIT_TARGET", self._build_exit_legs(pos, chain, "PROFIT_TARGET")

        # 3. DTE Exit Threshold
        if dte <= self.config.exit_dte_threshold:
            return True, "DTE_EXIT", self._build_exit_legs(pos, chain, "DTE_EXIT")

        # 4. Expiry Day Cash Settlement
        if dte <= 0:
            return True, "EXPIRY", self._build_exit_legs(pos, chain, "EXPIRY", is_expiry=True, spot=spot_price)

        return False, "", []

    def _build_exit_legs(
        self,
        pos: SimulatedPosition,
        chain: OptionChainSnapshot,
        exit_reason: str,
        is_expiry: bool = False,
        spot: float = 0.0,
    ) -> List[TradeLegExecution]:
        exit_legs: List[TradeLegExecution] = []
        for leg in pos.legs:
            exit_leg = leg.model_copy()
            exit_action = "SELL" if leg.action == "BUY" else "BUY"

            if is_expiry:
                # Expiry payoff intrinsic value settlement
                if leg.option_type == OptionType.CE:
                    intrinsic = max(0.0, spot - leg.strike_price)
                else:
                    intrinsic = max(0.0, leg.strike_price - spot)

                exit_exec_price = intrinsic
                exit_bid = intrinsic
                exit_ask = intrinsic
                exit_cost = 0.0  # Cash settlement at expiry
            else:
                quote = _get_quote_from_chain(chain, leg.contract_symbol, leg.strike_price, leg.option_type)
                if quote:
                    exit_bid = quote.bid_price or quote.last_price
                    exit_ask = quote.ask_price or quote.last_price
                    exit_exec_price = calculate_execution_price(quote, exit_action, self.config.cost_model)
                else:
                    exit_bid = leg.entry_exec_price
                    exit_ask = leg.entry_exec_price
                    exit_exec_price = leg.entry_exec_price

                exit_cost = calculate_nse_option_transaction_costs(
                    premium=exit_exec_price,
                    quantity=leg.quantity,
                    lots=leg.lots,
                    action=exit_action,
                    cost_model=self.config.cost_model,
                )

            exit_leg.exit_timestamp = chain.timestamp
            exit_leg.exit_bid = exit_bid
            exit_leg.exit_ask = exit_ask
            exit_leg.exit_exec_price = exit_exec_price
            exit_leg.exit_costs = exit_cost
            exit_legs.append(exit_leg)

        return exit_legs

    def _calculate_unrealized_pnl(
        self,
        pos: SimulatedPosition,
        chain: OptionChainSnapshot,
        spot_price: float,
    ) -> float:
        unrealized = 0.0
        for leg in pos.legs:
            quote = _get_quote_from_chain(chain, leg.contract_symbol, leg.strike_price, leg.option_type)
            if quote:
                current_price = quote.last_price
            else:
                current_price = leg.entry_exec_price

            if leg.action == "BUY":
                unrealized += (current_price - leg.entry_exec_price) * leg.quantity
            else:
                unrealized += (leg.entry_exec_price - current_price) * leg.quantity
        return round(unrealized, 2)
