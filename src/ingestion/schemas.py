"""
Data schemas for the Indian Options AI platform.

CRITICAL DESIGN DECISION:
- Option CONTRACTS contain ONLY static information (underlying, strike, expiry, etc.)
- Dynamic values (IV, Greeks, LTP, bid, ask, volume, OI) are stored as
  TIMESTAMPED MARKET OBSERVATIONS in separate models.
- This separation ensures proper time-series analysis and prevents treating
  a point-in-time observation as a permanent property.

All data crossing module boundaries uses these Pydantic models for type safety.
Every record carries: timestamp, source, ingestion_time, data_quality.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Enums
# =============================================================================

class OptionType(str, Enum):
    CE = "CE"
    PE = "PE"


class InstrumentType(str, Enum):
    INDEX = "INDEX"
    STOCK = "STOCK"


class Exchange(str, Enum):
    NSE = "NSE"
    BSE = "BSE"


class DataQualityStatus(str, Enum):
    """
    Data quality classification.
    Every piece of ingested data must be tagged with one of these.
    """
    GOOD = "GOOD"               # All fields present, values sensible
    PARTIAL = "PARTIAL"         # Some fields missing but usable
    STALE = "STALE"             # Data is older than freshness threshold
    SUSPECT = "SUSPECT"         # Values look abnormal (e.g., negative OI)
    UNAVAILABLE = "UNAVAILABLE" # Data could not be retrieved


class DataFreshnessLevel(str, Enum):
    """
    How fresh is this data? Displayed prominently on the dashboard.
    Never label cached/stale data as real-time.
    """
    LIVE = "LIVE"               # < live_threshold seconds old
    DELAYED = "DELAYED"         # < delayed_threshold
    STALE = "STALE"             # < stale_threshold
    END_OF_DAY = "END_OF_DAY"   # From a previous trading session
    UNAVAILABLE = "UNAVAILABLE" # No data available


class Moneyness(str, Enum):
    ITM = "ITM"
    ATM = "ATM"
    OTM = "OTM"


# =============================================================================
# Base record — every piece of data carries provenance
# =============================================================================

class DataRecord(BaseModel):
    """Base for all ingested data records."""
    timestamp: datetime = Field(description="When this data was generated/observed at source")
    source: str = Field(description="Data provider identifier (e.g., 'nse', 'kite', 'yfinance')")
    ingestion_time: datetime = Field(
        default_factory=datetime.now,
        description="When our system ingested this data",
    )
    data_quality: DataQualityStatus = Field(default=DataQualityStatus.GOOD)


# =============================================================================
# Underlying / Equity
# =============================================================================

class Quote(DataRecord):
    """Live quote for an underlying instrument."""
    symbol: str
    last_price: float
    change: Optional[float] = None
    change_pct: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None  # Previous close
    volume: Optional[int] = None
    bid: Optional[float] = None
    ask: Optional[float] = None


class OHLCVBar(BaseModel):
    """Single OHLCV candle. Not a DataRecord — used inside DataFrames."""
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float] = None


# =============================================================================
# Option Contract — STATIC information only
# =============================================================================

class OptionContract(BaseModel):
    """
    Static definition of an option contract.

    This model does NOT contain IV, Greeks, LTP, or any dynamic values.
    Those are stored as OptionQuote (timestamped observations).
    """
    underlying: str = Field(description="e.g., NIFTY, BANKNIFTY, RELIANCE")
    exchange: Exchange = Field(default=Exchange.NSE)
    instrument_type: InstrumentType = Field(default=InstrumentType.INDEX)
    option_type: OptionType
    strike_price: float
    expiry_date: date
    contract_symbol: Optional[str] = Field(
        default=None,
        description="Exchange-assigned contract symbol, if known",
    )
    lot_size: int = Field(default=1)

    @property
    def display_name(self) -> str:
        return f"{self.underlying} {self.strike_price} {self.option_type.value} {self.expiry_date}"


# =============================================================================
# Option Quote — TIMESTAMPED market observation
# =============================================================================

class OptionQuote(DataRecord):
    """
    A point-in-time market observation for a specific option contract.

    This is where dynamic values live: price, volume, OI, IV.
    IV is included here because NSE provides it in the option chain data.
    However, our own IV calculations (Phase 3) will go in ImpliedVolatilityObs.
    """
    underlying: str
    option_type: OptionType
    strike_price: float
    expiry_date: date

    # Price
    last_price: Optional[float] = None
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None

    # Volume & OI
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    change_in_oi: Optional[int] = None

    # IV from data source (not our calculation)
    implied_volatility: Optional[float] = Field(
        default=None,
        description="IV as reported by the data source. NOT our own calculation.",
    )

    # Computed fields (populated by our preprocessing)
    bid_ask_spread: Optional[float] = None
    bid_ask_spread_pct: Optional[float] = None
    volume_oi_ratio: Optional[float] = None

    @field_validator("last_price", "bid_price", "ask_price", mode="before")
    @classmethod
    def non_negative_price(cls, v: Any) -> Any:
        if v is not None and v < 0:
            return None  # Flag as unavailable, never invent
        return v

    @field_validator("volume", "open_interest", mode="before")
    @classmethod
    def non_negative_quantity(cls, v: Any) -> Any:
        if v is not None and v < 0:
            return None
        return v


# =============================================================================
# Greeks Observation — TIMESTAMPED (Phase 3, schema defined now)
# =============================================================================

class GreeksObservation(DataRecord):
    """
    Point-in-time Greeks for an option.
    Phase 3 will populate these. Defined now for schema completeness.
    """
    underlying: str
    option_type: OptionType
    strike_price: float
    expiry_date: date
    spot_price: float

    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    rho: Optional[float] = None

    # Model used to compute
    pricing_model: str = Field(default="black_scholes")
    iv_used: Optional[float] = None
    risk_free_rate: Optional[float] = None


# =============================================================================
# IV Observation — TIMESTAMPED (Phase 3, schema defined now)
# =============================================================================

class ImpliedVolatilityObs(DataRecord):
    """
    Our own calculated IV for an option (Phase 3).
    Separate from the IV reported by the data source in OptionQuote.
    """
    underlying: str
    option_type: OptionType
    strike_price: float
    expiry_date: date
    spot_price: float

    iv: Optional[float] = None
    solver_method: Optional[str] = None  # "newton_raphson", "brent", etc.
    solver_converged: bool = False
    solver_iterations: Optional[int] = None
    market_price_used: Optional[float] = None
    risk_free_rate: Optional[float] = None


# =============================================================================
# Option Chain — aggregated snapshot
# =============================================================================

class OptionStrikeRow(BaseModel):
    """One row in the option chain table: CE and PE data for a single strike."""
    strike_price: float
    expiry_date: date

    # CE side
    ce: Optional[OptionQuote] = None

    # PE side
    pe: Optional[OptionQuote] = None

    # Classification (set by our chain analyzer)
    moneyness: Optional[Moneyness] = None
    distance_from_atm: Optional[float] = None
    distance_from_atm_pct: Optional[float] = None


class OptionChainSnapshot(DataRecord):
    """
    Complete option chain for one underlying + one expiry at a point in time.
    """
    underlying: str
    expiry_date: date
    spot_price: float
    strikes: list[OptionStrikeRow] = Field(default_factory=list)

    # Metadata
    total_ce_oi: Optional[int] = None
    total_pe_oi: Optional[int] = None
    total_ce_volume: Optional[int] = None
    total_pe_volume: Optional[int] = None
    atm_strike: Optional[float] = None
    available_expiries: list[date] = Field(default_factory=list)


# =============================================================================
# Option Chain Analytics — output of chain analyzer
# =============================================================================

class OIConcentrationZone(BaseModel):
    """A strike with significant OI concentration."""
    strike_price: float
    option_type: OptionType
    open_interest: int
    change_in_oi: Optional[int] = None
    interpretation: str = Field(
        description="Probabilistic interpretation, e.g., 'Potential resistance zone — high call OI concentration'"
    )


class UnusualActivity(BaseModel):
    """A strike showing unusual volume or OI changes."""
    strike_price: float
    option_type: OptionType
    metric: str  # "volume", "oi_change"
    value: float
    average: Optional[float] = None
    std_dev: Optional[float] = None
    interpretation: str


class OptionChainAnalysis(DataRecord):
    """
    Output of the option chain analyzer.
    All interpretations use PROBABILISTIC language — never deterministic claims.
    """
    underlying: str
    expiry_date: date
    spot_price: float

    # Chain-level metrics
    put_call_ratio_oi: Optional[float] = None
    put_call_ratio_volume: Optional[float] = None
    max_pain_strike: Optional[float] = None
    atm_strike: Optional[float] = None
    atm_iv_ce: Optional[float] = None
    atm_iv_pe: Optional[float] = None

    # OI Analysis
    total_ce_oi: Optional[int] = None
    total_pe_oi: Optional[int] = None
    total_ce_volume: Optional[int] = None
    total_pe_volume: Optional[int] = None
    oi_concentration_zones: list[OIConcentrationZone] = Field(default_factory=list)

    # Unusual activity
    unusual_activity: list[UnusualActivity] = Field(default_factory=list)

    # Liquidity warnings
    liquidity_warnings: list[str] = Field(default_factory=list)

    # Overall interpretation (probabilistic)
    chain_interpretation: str = Field(
        default="Insufficient data for interpretation.",
        description="Summary interpretation using probabilistic language",
    )


# =============================================================================
# News — placeholder schema for future phases
# =============================================================================

class NewsItem(DataRecord):
    """A news article or event. Every item must have a verifiable source."""
    headline: str
    url: Optional[str] = None
    publisher: Optional[str] = None
    entities: list[str] = Field(default_factory=list)  # Tickers/symbols mentioned
    event_type: Optional[str] = None  # "earnings", "rbi_policy", "budget", etc.
    sentiment: Optional[str] = None  # "positive", "negative", "neutral"
    materiality: Optional[str] = None  # "high", "medium", "low"


# =============================================================================
# Data Quality Report
# =============================================================================

class DataQualityReport(BaseModel):
    """Report on the quality of an ingested dataset."""
    total_records: int = 0
    valid_records: int = 0
    partial_records: int = 0
    suspect_records: int = 0
    missing_fields: dict[str, int] = Field(default_factory=dict)
    validation_errors: list[str] = Field(default_factory=list)
    overall_quality: DataQualityStatus = DataQualityStatus.GOOD


# =============================================================================
# Phase 2 — Technical Analysis & Market Regime Schemas
# =============================================================================

class TimeFrame(str, Enum):
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    DAILY = "1d"
    WEEKLY = "1w"


class MarketRegimeType(str, Enum):
    STRONG_BULL = "STRONG_BULL"
    BULL = "BULL"
    SIDEWAYS = "SIDEWAYS"
    BEAR = "BEAR"
    STRONG_BEAR = "STRONG_BEAR"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    UNKNOWN = "UNKNOWN"


class CandlestickPattern(BaseModel):
    """
    Pattern detected by price action engine.
    Every pattern carries context, confidence, and invalidation rules.
    """
    timestamp: datetime
    timeframe: TimeFrame = TimeFrame.DAILY
    pattern: str  # "Doji", "Hammer", "Shooting Star", "Bullish Engulfing", "Bearish Engulfing", "Inside Bar", "Breakout", "Breakdown", "HH/HL", "LH/LL", "Gap Up", "Gap Down"
    context: str = Field(description="Market structure context around the pattern")
    historical_relevance: Optional[str] = Field(default=None, description="Statistical relevance or win rate range in similar context")
    confidence: float = Field(ge=0.0, le=1.0, description="Probabilistic confidence score")
    invalidation_conditions: str = Field(description="Specific price condition that invalidates this pattern")


class TechnicalFeatures(DataRecord):
    """
    Quantitative technical features computed at a specific timestamp.
    Time-series safe: Computed strictly using data <= timestamp.
    """
    symbol: str
    timeframe: TimeFrame = TimeFrame.DAILY
    close: float

    # Moving Averages
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None

    # Momentum & Trend Indicators
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    atr_14: Optional[float] = None
    adx_14: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None

    # Returns & Price Relatives
    returns_1d: Optional[float] = None
    returns_5d: Optional[float] = None
    returns_20d: Optional[float] = None
    price_to_sma20: Optional[float] = None
    price_to_sma50: Optional[float] = None
    price_to_sma200: Optional[float] = None
    trend_strength: Optional[float] = None  # 0 to 100 based on ADX / MA alignment
    momentum: Optional[float] = None  # Rate of change indicator

    # Realized Volatility (Annualized: std_dev * sqrt(252))
    realized_vol_5d: Optional[float] = None
    realized_vol_10d: Optional[float] = None
    realized_vol_20d: Optional[float] = None
    realized_vol_30d: Optional[float] = None
    realized_vol_60d: Optional[float] = None

    # Volume Features
    volume: Optional[int] = None
    volume_ratio_5d: Optional[float] = None  # Volume / 5-day SMA Volume
    volume_ratio_20d: Optional[float] = None # Volume / 20-day SMA Volume

    # Detected Patterns
    patterns: list[CandlestickPattern] = Field(default_factory=list)


class MarketRegimeResult(DataRecord):
    """
    Multi-signal market regime assessment.
    Returns composite regime with confidence, supporting/conflicting evidence, and invalidation rules.
    """
    symbol: str
    regime: MarketRegimeType = MarketRegimeType.UNKNOWN
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score from multi-indicator agreement")
    supporting_evidence: list[str] = Field(default_factory=list)
    conflicting_evidence: list[str] = Field(default_factory=list)
    invalidation_conditions: list[str] = Field(default_factory=list)
    vix_value: Optional[float] = None
    nifty_trend: Optional[str] = None
    banknifty_trend: Optional[str] = None
    breadth_ratio: Optional[float] = None


class IndiaVIXRecord(DataRecord):
    """India VIX observation."""
    value: float
    change: Optional[float] = None
    change_pct: Optional[float] = None

