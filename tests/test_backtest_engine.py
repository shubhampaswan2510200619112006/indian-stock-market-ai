"""
Tests for Chronological Event-Driven Options Backtest Engine.
"""

from datetime import date
import pytest

from src.backtesting.models import (
    BacktestConfig,
    CostModelType,
    ExecutionCostModel,
    LiquidityMode,
)
from src.backtesting.engine import BacktestEngine
from src.backtesting.execution import (
    calculate_execution_price,
    calculate_nse_option_transaction_costs,
    evaluate_liquidity_filter,
)
from src.ingestion.schemas import DataQualityStatus, OptionQuote, OptionType


def test_execution_price_buy_sell():
    quote = OptionQuote(
        contract_symbol="NIFTY26JAN24000CE",
        underlying="NIFTY",
        option_type=OptionType.CE,
        strike_price=24000.0,
        expiry_date=date(2026, 1, 28),
        timestamp="2026-01-01T10:00:00",
        last_price=100.0,
        bid_price=99.0,
        ask_price=101.0,
        source="TEST",
    )
    model = ExecutionCostModel(slippage_pct=0.01)  # 1% slippage
    
    buy_price = calculate_execution_price(quote, "BUY", model)
    sell_price = calculate_execution_price(quote, "SELL", model)
    
    # BUY: ask (101) * 1.01 = 102.01
    assert buy_price == 102.01
    # SELL: bid (99) * 0.99 = 98.01
    assert sell_price == 98.01


def test_nse_transaction_costs():
    cost_model = ExecutionCostModel()
    # Premium 100, 25 qty (1 lot)
    costs_buy = calculate_nse_option_transaction_costs(100.0, 25, 1, "BUY", cost_model)
    costs_sell = calculate_nse_option_transaction_costs(100.0, 25, 1, "SELL", cost_model)
    
    assert costs_buy > 0.0
    assert costs_sell > costs_buy  # Sell includes STT


def test_liquidity_filter():
    good_quote = OptionQuote(
        contract_symbol="NIFTY26JAN24000CE",
        underlying="NIFTY",
        option_type=OptionType.CE,
        strike_price=24000.0,
        expiry_date=date(2026, 1, 28),
        timestamp="2026-01-01T10:00:00",
        last_price=100.0,
        bid_price=99.0,
        ask_price=101.0,
        volume=500,
        open_interest=5000,
        source="TEST",
    )
    is_liquid, msg = evaluate_liquidity_filter(good_quote, LiquidityMode.NORMAL)
    assert is_liquid is True

    bad_oi_quote = good_quote.model_copy()
    bad_oi_quote.open_interest = 10
    is_liquid_bad, _ = evaluate_liquidity_filter(bad_oi_quote, LiquidityMode.NORMAL)
    assert is_liquid_bad is False


def test_backtest_engine_synthetic_run():
    config = BacktestConfig(
        symbol="NIFTY",
        start_date=date(2030, 1, 1),
        end_date=date(2030, 1, 20),
        initial_equity=1_000_000.0,
        strategy_name="Bull Call Spread",
        min_strategy_score=50.0,
        use_synthetic_if_unavailable=True,
    )
    engine = BacktestEngine(config)
    result = engine.run()

    assert result.data_source == "SYNTHETIC TEST FIXTURE"
    assert "SYNTHETIC TEST DATA — SOFTWARE TESTING ONLY" in result.critical_labels
    assert len(result.equity_curve) > 0
    assert result.metrics is not None
