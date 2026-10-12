"""
SQLAlchemy ORM models.

CRITICAL DESIGN:
- options_contracts: STATIC contract info only (underlying, strike, expiry, lot_size)
- options_quotes: TIMESTAMPED market observations (LTP, bid, ask, volume, OI, source IV)
- options_greeks: TIMESTAMPED Greek calculations (Phase 3)
- implied_volatility: TIMESTAMPED IV calculations (Phase 3)
- options_chain_snapshots: Point-in-time metadata for a full chain fetch

Every table includes: created_at, source, data_quality.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# =============================================================================
# Underlyings — NIFTY, BANKNIFTY, stocks
# =============================================================================

class UnderlyingDB(Base):
    __tablename__ = "underlyings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    exchange = Column(String(10), nullable=False, default="NSE")
    instrument_type = Column(String(20), nullable=False)  # INDEX, STOCK
    lot_size = Column(Integer, nullable=False, default=1)
    tick_size = Column(Float, default=0.05)
    enabled = Column(Integer, default=1)  # 1=enabled, 0=disabled (SQLite-compatible bool)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# =============================================================================
# Equity Prices — OHLCV history for underlyings
# =============================================================================

class EquityPriceDB(Base):
    __tablename__ = "equity_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False, index=True)
    date = Column(Date, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    adjusted_close = Column(Float)
    source = Column(String(50), nullable=False)
    data_quality = Column(String(20), default="GOOD")
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("symbol", "date", "source", name="uq_equity_price"),
        Index("idx_equity_symbol_date", "symbol", "date"),
    )


# =============================================================================
# Options Contracts — STATIC information only
# =============================================================================

class OptionsContractDB(Base):
    __tablename__ = "options_contracts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    underlying = Column(String(50), nullable=False, index=True)
    exchange = Column(String(10), nullable=False, default="NSE")
    instrument_type = Column(String(20), nullable=False)  # INDEX_OPTION, STOCK_OPTION
    option_type = Column(String(2), nullable=False)  # CE, PE
    strike_price = Column(Float, nullable=False)
    expiry_date = Column(Date, nullable=False, index=True)
    contract_symbol = Column(String(100))
    lot_size = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    quotes = relationship("OptionsQuoteDB", back_populates="contract", lazy="dynamic")

    __table_args__ = (
        UniqueConstraint(
            "underlying", "option_type", "strike_price", "expiry_date",
            name="uq_option_contract",
        ),
        Index("idx_contract_lookup", "underlying", "expiry_date", "strike_price"),
    )


# =============================================================================
# Options Quotes — TIMESTAMPED market observations
# =============================================================================

class OptionsQuoteDB(Base):
    __tablename__ = "options_quotes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("options_contracts.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)

    # Price
    last_price = Column(Float)
    bid_price = Column(Float)
    ask_price = Column(Float)

    # Volume & OI
    volume = Column(Integer)
    open_interest = Column(Integer)
    change_in_oi = Column(Integer)

    # IV from data source (NOT our calculation)
    implied_volatility_source = Column(Float)

    # Computed spreads
    bid_ask_spread = Column(Float)
    bid_ask_spread_pct = Column(Float)
    volume_oi_ratio = Column(Float)

    # Provenance
    source = Column(String(50), nullable=False)
    ingestion_time = Column(DateTime, default=func.now())
    data_quality = Column(String(20), default="GOOD")

    # Relationship
    contract = relationship("OptionsContractDB", back_populates="quotes")

    __table_args__ = (
        Index("idx_quote_contract_time", "contract_id", "timestamp"),
    )


# =============================================================================
# Options Chain Snapshots — metadata for a full chain fetch
# =============================================================================

class OptionsChainSnapshotDB(Base):
    __tablename__ = "options_chain_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    underlying = Column(String(50), nullable=False, index=True)
    expiry_date = Column(Date, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    spot_price = Column(Float, nullable=False)

    # Aggregates
    total_ce_oi = Column(Integer)
    total_pe_oi = Column(Integer)
    total_ce_volume = Column(Integer)
    total_pe_volume = Column(Integer)
    put_call_ratio_oi = Column(Float)
    put_call_ratio_volume = Column(Float)
    max_pain_strike = Column(Float)
    atm_strike = Column(Float)

    # Full snapshot data as JSON (for replay/audit)
    snapshot_data = Column(JSON)

    # Provenance
    source = Column(String(50), nullable=False)
    ingestion_time = Column(DateTime, default=func.now())
    data_quality = Column(String(20), default="GOOD")

    __table_args__ = (
        Index("idx_snapshot_lookup", "underlying", "expiry_date", "timestamp"),
    )


# =============================================================================
# Options Greeks — TIMESTAMPED (Phase 3, table created now)
# =============================================================================

class OptionsGreeksDB(Base):
    __tablename__ = "options_greeks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("options_contracts.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    spot_price = Column(Float, nullable=False)

    delta = Column(Float)
    gamma = Column(Float)
    theta = Column(Float)
    vega = Column(Float)
    rho = Column(Float)

    pricing_model = Column(String(50), default="black_scholes")
    iv_used = Column(Float)
    risk_free_rate = Column(Float)

    source = Column(String(50), nullable=False)
    ingestion_time = Column(DateTime, default=func.now())
    data_quality = Column(String(20), default="GOOD")

    __table_args__ = (
        Index("idx_greeks_contract_time", "contract_id", "timestamp"),
    )


# =============================================================================
# Implied Volatility — TIMESTAMPED (Phase 3, table created now)
# =============================================================================

class ImpliedVolatilityDB(Base):
    __tablename__ = "implied_volatility"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("options_contracts.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    spot_price = Column(Float, nullable=False)

    iv = Column(Float)
    solver_method = Column(String(50))
    solver_converged = Column(Integer)  # 1/0 for SQLite compat
    solver_iterations = Column(Integer)
    market_price_used = Column(Float)
    risk_free_rate = Column(Float)

    source = Column(String(50), nullable=False)
    ingestion_time = Column(DateTime, default=func.now())
    data_quality = Column(String(20), default="GOOD")

    __table_args__ = (
        Index("idx_iv_contract_time", "contract_id", "timestamp"),
    )


# =============================================================================
# Data Quality Logs
# =============================================================================

class DataQualityLogDB(Base):
    __tablename__ = "data_quality_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=func.now())
    provider = Column(String(50), nullable=False)
    operation = Column(String(100), nullable=False)  # e.g., "fetch_option_chain"
    symbol = Column(String(50))
    total_records = Column(Integer, default=0)
    valid_records = Column(Integer, default=0)
    partial_records = Column(Integer, default=0)
    suspect_records = Column(Integer, default=0)
    missing_fields = Column(JSON)  # {"field_name": count}
    errors = Column(JSON)  # List of error messages
    overall_quality = Column(String(20), default="GOOD")
    duration_seconds = Column(Float)


# =============================================================================
# Phase 2 — Technical Features & Market Regime Tables
# =============================================================================

class TechnicalFeatureDB(Base):
    __tablename__ = "technical_features"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, default="1d")
    close = Column(Float, nullable=False)

    sma_20 = Column(Float)
    sma_50 = Column(Float)
    sma_200 = Column(Float)
    ema_12 = Column(Float)
    ema_26 = Column(Float)

    rsi_14 = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    macd_hist = Column(Float)
    atr_14 = Column(Float)
    adx_14 = Column(Float)
    bb_upper = Column(Float)
    bb_middle = Column(Float)
    bb_lower = Column(Float)

    returns_1d = Column(Float)
    returns_5d = Column(Float)
    returns_20d = Column(Float)
    price_to_sma20 = Column(Float)
    price_to_sma50 = Column(Float)
    price_to_sma200 = Column(Float)
    trend_strength = Column(Float)
    momentum = Column(Float)

    realized_vol_5d = Column(Float)
    realized_vol_10d = Column(Float)
    realized_vol_20d = Column(Float)
    realized_vol_30d = Column(Float)
    realized_vol_60d = Column(Float)

    volume = Column(Integer)
    volume_ratio_5d = Column(Float)
    volume_ratio_20d = Column(Float)

    patterns = Column(JSON)  # List of dicts representing CandlestickPattern
    source = Column(String(50), nullable=False, default="yfinance")
    data_quality = Column(String(20), default="GOOD")
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("symbol", "timestamp", "timeframe", name="uq_tech_features"),
        Index("idx_tech_symbol_time", "symbol", "timestamp", "timeframe"),
    )


class MarketRegimeDB(Base):
    __tablename__ = "market_regimes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    regime = Column(String(30), nullable=False)
    confidence = Column(Float, nullable=False)
    supporting_evidence = Column(JSON)  # List of strings
    conflicting_evidence = Column(JSON)  # List of strings
    invalidation_conditions = Column(JSON)  # List of strings
    vix_value = Column(Float)
    nifty_trend = Column(String(30))
    banknifty_trend = Column(String(30))
    breadth_ratio = Column(Float)

    source = Column(String(50), nullable=False, default="engine")
    data_quality = Column(String(20), default="GOOD")
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        Index("idx_regime_symbol_time", "symbol", "timestamp"),
    )


# =============================================================================
# Phase 7: Live Market & News Tables
# =============================================================================

class LiveQuoteDB(Base):
    __tablename__ = "live_quotes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False, index=True)
    provider_symbol = Column(String(50))
    last_price = Column(Float, nullable=False)
    previous_close = Column(Float)
    change = Column(Float)
    change_pct = Column(Float)
    day_high = Column(Float)
    day_low = Column(Float)
    volume = Column(Integer)
    provider_timestamp = Column(String(50))
    received_timestamp = Column(String(50))
    normalized_timestamp = Column(String(50))
    latency_ms = Column(Float)
    source = Column(String(50))
    status_label = Column(String(30))
    created_at = Column(DateTime, default=func.now())


class LiveCandleDB(Base):
    __tablename__ = "live_candles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False, index=True)
    timeframe = Column(String(20), nullable=False)
    timestamp = Column(String(50), nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    source = Column(String(50))
    received_at = Column(String(50))
    created_at = Column(DateTime, default=func.now())


class NewsArticleDB(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(Text, nullable=False)
    url = Column(Text)
    source_name = Column(String(100))
    source_authority = Column(String(50))
    published_at = Column(String(50))
    received_at = Column(String(50))
    processed_at = Column(String(50))
    ingestion_latency_ms = Column(Float)
    processing_latency_ms = Column(Float)
    total_latency_ms = Column(Float)
    entity = Column(String(50), index=True)
    sector = Column(String(50))
    event_type = Column(String(50))
    sentiment = Column(String(30))
    sentiment_score = Column(Float)
    materiality = Column(String(30))
    materiality_reason = Column(Text)
    created_at = Column(DateTime, default=func.now())


class ProviderHealthDB(Base):
    __tablename__ = "provider_health"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_name = Column(String(100), nullable=False, index=True)
    provider_type = Column(String(50), nullable=False)
    is_healthy = Column(String(10))
    status_label = Column(String(50))
    latency_ms = Column(Float)
    error_count = Column(Integer, default=0)
    last_check_at = Column(DateTime, default=func.now())


class LiveMarketAnalysisDB(Base):
    __tablename__ = "live_market_analysis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False, index=True)
    timestamp = Column(String(50), nullable=False)
    market_regime = Column(String(50))
    directional_bias = Column(String(30))
    confidence = Column(Float)
    research_setup = Column(String(50))
    recommended_strategy = Column(String(50))
    reasoning = Column(Text)
    created_at = Column(DateTime, default=func.now())


# =============================================================================
# Phase 8: Paper Trading Tables
# =============================================================================

class PaperSessionDB(Base):
    __tablename__ = "paper_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), unique=True, nullable=False, index=True)
    started_at = Column(DateTime, nullable=False)
    stopped_at = Column(DateTime)
    starting_capital = Column(Float, nullable=False)
    execution_mode = Column(String(20), nullable=False, default="PAPER")
    status = Column(String(20), nullable=False, default="STARTED")
    provider_config = Column(JSON)
    risk_config = Column(JSON)
    model_versions = Column(JSON)
    created_at = Column(DateTime, default=func.now())


class PaperOrderDB(Base):
    __tablename__ = "paper_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(50), unique=True, nullable=False, index=True)
    session_id = Column(String(50), index=True)
    created_at = Column(DateTime, nullable=False)
    decision_timestamp = Column(DateTime)
    symbol = Column(String(50), nullable=False, index=True)
    instrument_type = Column(String(30))
    strike = Column(Float)
    expiry = Column(Date)
    option_type = Column(String(5))
    side = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False)
    order_type = Column(String(20), nullable=False)
    limit_price = Column(Float)
    stop_price = Column(Float)
    strategy_id = Column(String(50))
    strategy_name = Column(String(100))
    signal_id = Column(String(50))
    model_version = Column(String(50))
    execution_mode = Column(String(20), nullable=False, default="PAPER")
    status = Column(String(20), nullable=False, index=True)
    filled_quantity = Column(Integer, default=0)
    average_fill_price = Column(Float)
    submitted_at = Column(DateTime)
    filled_at = Column(DateTime)
    rejection_reason = Column(Text)
    expiry_type = Column(String(10), default="DAY")
    expiry_date_gtd = Column(Date)


class PaperFillDB(Base):
    __tablename__ = "paper_fills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fill_id = Column(String(50), unique=True, nullable=False, index=True)
    order_id = Column(String(50), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    fill_quantity = Column(Integer, nullable=False)
    fill_price = Column(Float, nullable=False)
    fill_timestamp = Column(DateTime, nullable=False)
    provider_timestamp = Column(DateTime, nullable=False)
    received_timestamp = Column(DateTime, nullable=False)
    execution_timestamp = Column(DateTime, nullable=False)
    source_provider = Column(String(50), nullable=False)
    price_source = Column(String(50), nullable=False)
    price_source_description = Column(Text)
    data_status_at_fill = Column(String(30), nullable=False)
    slippage_applied = Column(Float)
    transaction_costs = Column(Float)
    quote_age_seconds = Column(Float)
    execution_mode = Column(String(20), nullable=False, default="PAPER")
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("order_id", "provider_timestamp", "symbol", name="uq_paper_fill_idempotent"),
    )


class PaperPositionDB(Base):
    __tablename__ = "paper_positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    position_id = Column(String(50), unique=True, nullable=False, index=True)
    session_id = Column(String(50), index=True)
    symbol = Column(String(50), nullable=False, index=True)
    instrument_type = Column(String(30))
    quantity = Column(Integer, nullable=False)
    average_entry_price = Column(Float, nullable=False)
    current_market_price = Column(Float)
    market_value = Column(Float)
    realized_pnl = Column(Float, default=0.0)
    unrealized_pnl = Column(Float)
    entry_timestamp = Column(DateTime)
    last_mark_timestamp = Column(DateTime)
    last_mark_status = Column(String(30), default="UNAVAILABLE")
    strategy = Column(String(100))
    execution_mode = Column(String(20), nullable=False, default="PAPER")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class PaperPortfolioSnapshotDB(Base):
    __tablename__ = "paper_portfolio_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    cash = Column(Float, nullable=False)
    equity = Column(Float, nullable=False)
    available_cash = Column(Float)
    margin_used = Column(Float, default=0.0)
    gross_exposure = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    daily_pnl = Column(Float, default=0.0)
    peak_equity = Column(Float)
    current_drawdown_pct = Column(Float, default=0.0)
    max_drawdown_pct = Column(Float, default=0.0)
    open_positions_count = Column(Integer, default=0)
    execution_mode = Column(String(20), nullable=False, default="PAPER")
    created_at = Column(DateTime, default=func.now())


class PaperTradeJournalDB(Base):
    __tablename__ = "paper_trade_journal"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(String(50), unique=True, nullable=False, index=True)
    session_id = Column(String(50), index=True)
    symbol = Column(String(50), nullable=False, index=True)
    strategy = Column(String(100))
    direction = Column(String(10), nullable=False)
    entry_timestamp = Column(DateTime)
    exit_timestamp = Column(DateTime)
    quantity = Column(Integer, nullable=False)
    entry_price = Column(Float)
    exit_price = Column(Float)
    gross_pnl = Column(Float, default=0.0)
    fees = Column(Float, default=0.0)
    slippage = Column(Float, default=0.0)
    net_pnl = Column(Float, default=0.0)
    holding_period_seconds = Column(Float)
    model_version = Column(String(50))
    regime = Column(String(50))
    evidence_label = Column(String(50))
    execution_mode = Column(String(20), nullable=False, default="PAPER")
    created_at = Column(DateTime, default=func.now())


class PaperRiskEventDB(Base):
    __tablename__ = "paper_risk_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), index=True)
    event_type = Column(String(50), nullable=False)
    triggered_at = Column(DateTime, nullable=False)
    threshold = Column(Float)
    actual_value = Column(Float)
    details = Column(Text)
    execution_mode = Column(String(20), nullable=False, default="PAPER")
    created_at = Column(DateTime, default=func.now())


# =============================================================================
# Phase 9: Legitimate Market & Options Data Infrastructure Models
# =============================================================================

class DataProviderDB(Base):
    __tablename__ = "data_providers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(String(50), unique=True, nullable=False, index=True)
    provider_name = Column(String(100), nullable=False)
    provider_type = Column(String(50), nullable=False)
    licensing_status = Column(String(50), default="UNVERIFIED")
    terms_of_use = Column(Text)
    is_active = Column(Integer, default=1)
    rate_limit_per_minute = Column(Integer, default=60)
    cost_tier = Column(String(50), default="FREE")
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ProviderCapabilityDB(Base):
    __tablename__ = "provider_capabilities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(String(50), nullable=False, index=True)
    capability_name = Column(String(50), nullable=False)
    is_supported = Column(Integer, default=0)
    status_label = Column(String(50), default="UNVERIFIED")
    details = Column(Text)
    created_at = Column(DateTime, default=func.now())


class ProviderVerificationDB(Base):
    __tablename__ = "provider_verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    verification_id = Column(String(50), unique=True, nullable=False, index=True)
    provider_name = Column(String(100), nullable=False, index=True)
    capability = Column(String(50), nullable=False)
    verification_timestamp = Column(DateTime, nullable=False)
    test_instrument = Column(String(50), nullable=False)
    observed_provider_timestamp = Column(DateTime)
    observed_received_timestamp = Column(DateTime)
    observed_latency_ms = Column(Float)
    observed_fields = Column(JSON)
    verification_method = Column(String(50), nullable=False)
    result = Column(String(20), nullable=False)  # PASS, FAIL, WARNING
    status = Column(String(30), nullable=False)  # VERIFIED_REAL_TIME, VERIFIED_DELAYED, etc.
    evidence_reference = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())


class InstrumentMasterDB(Base):
    __tablename__ = "instrument_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    exchange = Column(String(20), nullable=False, default="NSE")
    asset_class = Column(String(30), nullable=False)  # INDEX, EQUITY, OPTION, FUTURE
    lot_size = Column(Integer, nullable=False, default=1)
    tick_size = Column(Float, default=0.05)
    strike_step = Column(Float, default=50.0)
    is_tradable = Column(Integer, default=1)
    expiry_frequency = Column(String(20), default="MONTHLY")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class MarketObservationDB(Base):
    __tablename__ = "market_observations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    observation_id = Column(String(50), unique=True, nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)
    provider_symbol = Column(String(50))
    symbol = Column(String(50), nullable=False, index=True)
    provider_timestamp = Column(DateTime, nullable=False, index=True)
    received_timestamp = Column(DateTime, nullable=False)
    processed_timestamp = Column(DateTime, nullable=False)
    last_price = Column(Float)
    bid_price = Column(Float)
    ask_price = Column(Float)
    volume = Column(Integer)
    open_interest = Column(Integer)
    data_status = Column(String(30), nullable=False)
    validation_status = Column(String(30), nullable=False)
    is_executable = Column(Integer, default=0)
    raw_payload = Column(JSON)
    batch_id = Column(String(50), index=True)
    dataset_id = Column(String(50))
    dataset_version = Column(String(50))
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        Index("idx_obs_sym_prov_ts", "symbol", "provider", "provider_timestamp"),
    )


class IntradayCandleDB(Base):
    __tablename__ = "intraday_candles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False, index=True)
    timeframe = Column(String(20), nullable=False, index=True)
    candle_timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False, default=0)
    is_derived_interval = Column(Integer, default=0)  # 1 if resampled locally
    source_provider = Column(String(50), nullable=False)
    data_status = Column(String(30), default="HISTORICAL")
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        Index("idx_candle_sym_tf_time", "symbol", "timeframe", "candle_timestamp"),
    )


class DataQualityEventDB(Base):
    __tablename__ = "data_quality_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(50), unique=True, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    rule_violated = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)  # WARNING, ERROR, QUARANTINE
    details = Column(Text)
    observation_id = Column(String(50))
    provider = Column(String(50))
    batch_id = Column(String(50))
    created_at = Column(DateTime, default=func.now())


class IngestionBatchDB(Base):
    __tablename__ = "ingestion_batches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(50), unique=True, nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    requested_instruments = Column(JSON)
    records_received = Column(Integer, default=0)
    records_accepted = Column(Integer, default=0)
    records_quarantined = Column(Integer, default=0)
    status = Column(String(30), nullable=False, default="RUNNING")
    checkpoint_data = Column(JSON)
    error_log = Column(Text)
    created_at = Column(DateTime, default=func.now())


class DatasetSnapshotDB(Base):
    __tablename__ = "dataset_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String(50), unique=True, nullable=False, index=True)
    dataset_id = Column(String(50), nullable=False, index=True)
    dataset_version = Column(String(30), nullable=False, index=True)
    description = Column(Text)
    date_range_start = Column(Date)
    date_range_end = Column(Date)
    observation_count = Column(Integer, default=0)
    ltp_coverage_pct = Column(Float, default=0.0)
    bid_ask_coverage_pct = Column(Float, default=0.0)
    oi_coverage_pct = Column(Float, default=0.0)
    volume_coverage_pct = Column(Float, default=0.0)
    iv_coverage_pct = Column(Float, default=0.0)
    quality_status = Column(String(30), default="UNVERIFIED")
    manifest = Column(JSON)
    is_immutable = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())


class DataLineageDB(Base):
    __tablename__ = "data_lineage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lineage_id = Column(String(50), unique=True, nullable=False, index=True)
    target_artifact_type = Column(String(50), nullable=False)  # FEATURE_ROW, PREDICTION, BACKTEST_RUN
    target_artifact_id = Column(String(50), nullable=False, index=True)
    dataset_snapshot_id = Column(String(50))
    source_observation_ids = Column(JSON)
    feature_version = Column(String(50))
    lineage_hash = Column(String(64))
    created_at = Column(DateTime, default=func.now())


class MarketCalendarDB(Base):
    __tablename__ = "market_calendar"

    id = Column(Integer, primary_key=True, autoincrement=True)
    calendar_date = Column(Date, unique=True, nullable=False, index=True)
    is_trading_day = Column(Integer, default=1)
    session_type = Column(String(30), default="REGULAR")  # REGULAR, SPECIAL_MUHURAT, CLOSED
    market_open_time = Column(String(10), default="09:15:00")
    market_close_time = Column(String(10), default="15:30:00")
    holiday_name = Column(String(100))
    is_expiry_day = Column(Integer, default=0)
    expiry_type = Column(String(30), default="NONE")  # WEEKLY, MONTHLY, NONE
    created_at = Column(DateTime, default=func.now())


class CorporateActionDB(Base):
    __tablename__ = "corporate_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False, index=True)
    action_type = Column(String(50), nullable=False)  # SPLIT, BONUS, DIVIDEND, SYMBOL_CHANGE
    ex_date = Column(Date, nullable=False, index=True)
    record_date = Column(Date)
    ratio_from = Column(Float)
    ratio_to = Column(Float)
    dividend_amount = Column(Float)
    adjustment_factor = Column(Float, default=1.0)
    source = Column(String(50), nullable=False)
    notes = Column(Text)
    is_applied = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())


# =============================================================================
# Phase 16: Bhavcopy Staging (provenance) and Options EOD records
# =============================================================================

class BhavcopyStagingDB(Base):
    """
    Provenance record for each downloaded NSE Bhavcopy archive.
    Records raw artifact metadata BEFORE parsing.
    Idempotent: unique constraint on (trade_date, source_url).
    """
    __tablename__ = "bhavcopy_staging"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_date = Column(Date, nullable=False, index=True)
    source_url = Column(Text, nullable=False)
    retrieval_timestamp = Column(DateTime, nullable=False)
    file_size_bytes = Column(Integer, default=0)
    sha256_hash = Column(String(64), nullable=False)
    local_raw_path = Column(Text, nullable=False)
    download_status = Column(String(30), nullable=False)  # SUCCESS, NOT_FOUND, ERROR, CACHED
    parse_status = Column(String(30), default="PENDING")  # PENDING, SUCCESS, PARTIAL, ERROR
    records_inserted = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("trade_date", "source_url", name="uq_bhavcopy_staging"),
        Index("idx_bhavcopy_staging_date", "trade_date"),
    )


class BhavcopyCandleDB(Base):
    """
    NSE FO Bhavcopy options EOD record.

    CRITICAL DATA INTEGRITY:
    - bid_price and ask_price are ALWAYS NULL. Bhavcopy has no bid/ask.
    - data_status is SETTLEMENT_PRICE_ONLY for all records.
    - DO NOT treat settlement_price as executable bid/ask data.
    - settlement_price is the NSE EOD settlement value only.

    Idempotent: unique constraint on (trade_date, underlying, expiry_date, strike_price, option_type).
    """
    __tablename__ = "bhavcopy_candles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_date = Column(Date, nullable=False, index=True)
    underlying = Column(String(50), nullable=False, index=True)
    expiry_date = Column(Date, index=True)
    strike_price = Column(Float)
    option_type = Column(String(2))               # CE or PE
    open_interest = Column(Integer)
    change_in_oi = Column(Integer)
    volume = Column(Integer)
    settlement_price = Column(Float)
    # Bid/ask are deliberately absent — Bhavcopy has no bid/ask data
    bid_price = Column(Float, nullable=True, default=None)   # ALWAYS NULL
    ask_price = Column(Float, nullable=True, default=None)   # ALWAYS NULL
    underlying_price = Column(Float)

    # Data status: always SETTLEMENT_PRICE_ONLY for Bhavcopy records
    data_status = Column(String(40), nullable=False, default="SETTLEMENT_PRICE_ONLY")
    source = Column(String(50), nullable=False, default="NSE_FO_BHAVCOPY")
    data_quality = Column(String(20), default="GOOD")
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "trade_date", "underlying", "expiry_date", "strike_price", "option_type",
            name="uq_bhavcopy_candle",
        ),
        Index("idx_bhavcopy_candle_lookup", "trade_date", "underlying", "expiry_date"),
    )


# =============================================================================
# Phase 16: FII/DII Participant Flow Data
# =============================================================================

class FIIDIIFlowDB(Base):
    """
    Daily FII and DII participant-wise net buy/sell flow data.
    Source: NSE participant-wise trading data (public).

    DATA INFRASTRUCTURE ONLY — not used for alpha research conclusions.
    """
    __tablename__ = "fii_dii_flows"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_date = Column(Date, nullable=False, index=True)

    # FII (Foreign Institutional Investor) flows — INR crores, net = buy - sell
    fii_net_buy_sell = Column(Float)               # Net across all segments
    fii_index_futures_net = Column(Float)
    fii_index_options_net = Column(Float)
    fii_stock_futures_net = Column(Float)
    fii_stock_options_net = Column(Float)
    fii_equity_net = Column(Float)                 # Cash market

    # DII (Domestic Institutional Investor) flows
    dii_net_buy_sell = Column(Float)
    dii_equity_net = Column(Float)

    # Provenance
    source = Column(String(50), nullable=False, default="NSE_PARTICIPANT_DATA")
    retrieval_timestamp = Column(DateTime, nullable=False)
    freshness_level = Column(String(20), default="END_OF_DAY")
    data_quality = Column(String(20), default="GOOD")
    raw_payload = Column(JSON)                     # Original JSON response for audit
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("trade_date", "source", name="uq_fii_dii_flow"),
        Index("idx_fii_dii_date", "trade_date"),
    )


# =============================================================================
# Phase 16: Macro Features
# =============================================================================

class MacroFeatureDB(Base):
    """
    Daily/intraday macro market features.
    Sources: yfinance (public, delayed) for India VIX, USD/INR, crude oil, GIFT Nifty.

    IMPORTANT:
    - All values are from public data feeds (typically delayed 15-20 min for live).
    - freshness_level reflects actual data age, not aspirational timeliness.
    - Missing values are NULL — not interpolated or fabricated.
    - data_quality reflects source reliability, not investment suitability.
    """
    __tablename__ = "macro_features"

    id = Column(Integer, primary_key=True, autoincrement=True)
    observation_date = Column(Date, nullable=False, index=True)
    observation_timestamp = Column(DateTime, index=True)  # For intraday records

    # India VIX — source: ^INDIAVIX via yfinance (delayed ~15 min or EOD)
    india_vix = Column(Float)
    india_vix_change = Column(Float)
    india_vix_freshness = Column(String(20))       # LIVE/DELAYED/STALE/END_OF_DAY/UNAVAILABLE

    # GIFT Nifty — SGX/NSE IFSC pre-market indicator
    gift_nifty = Column(Float)
    gift_nifty_change_pct = Column(Float)
    gift_nifty_freshness = Column(String(20))

    # USD/INR — USDINR=X via yfinance
    usd_inr = Column(Float)
    usd_inr_change_pct = Column(Float)
    usd_inr_freshness = Column(String(20))

    # Crude oil (WTI front-month) — CL=F via yfinance
    crude_wti = Column(Float)
    crude_wti_change_pct = Column(Float)
    crude_wti_freshness = Column(String(20))

    # MCX Crude (India-traded) — CRUDEOIL1! or ^MCX (where available)
    crude_mcx = Column(Float)
    crude_mcx_freshness = Column(String(20))

    # Provenance
    source = Column(String(50), nullable=False, default="yfinance")
    retrieval_timestamp = Column(DateTime, nullable=False)
    data_quality = Column(String(20), default="GOOD")
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("observation_date", "source", name="uq_macro_features"),
        Index("idx_macro_date", "observation_date"),
    )


# =============================================================================
# User Accounts, API Tokens & Multi-Tenant Paper Trading State
# =============================================================================

class UserAccountDB(Base):
    """Trader account credentials and starting capital."""
    __tablename__ = "users"

    id = Column(String(50), primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    salt = Column(String(64), nullable=False)
    password_hash = Column(String(128), nullable=False)
    starting_capital = Column(Float, default=1_000_000.0)
    created_at = Column(String(50), nullable=False)
    last_login = Column(String(50))


class ApiTokenDB(Base):
    """Bearer/API access tokens with user binding."""
    __tablename__ = "api_tokens"

    token = Column(String(128), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False, index=True)
    description = Column(String(100))
    created_at = Column(String(50), nullable=False)
    last_used_at = Column(String(50))


class UserPaperStateDB(Base):
    """Durable JSON-serialized portfolio, orders, and fills per user."""
    __tablename__ = "user_paper_states"

    user_id = Column(String(50), primary_key=True)
    session_id = Column(String(50))
    portfolio_state = Column(JSON, nullable=False)
    orders_state = Column(JSON)
    fills_state = Column(JSON)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())




