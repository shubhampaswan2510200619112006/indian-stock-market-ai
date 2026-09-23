"""
Repository pattern for database operations.

All queries return Pydantic models or DataFrames, never raw ORM objects.
The repository hides database-specific implementation details.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Optional

import pandas as pd
from sqlalchemy import desc, and_
from sqlalchemy.orm import Session

from src.database.connection import get_session
from src.database.models import (
    DataQualityLogDB,
    EquityPriceDB,
    OptionsChainSnapshotDB,
    OptionsContractDB,
    OptionsQuoteDB,
    UnderlyingDB,
)
from src.ingestion.schemas import (
    DataQualityStatus,
    OptionChainSnapshot,
    OptionQuote,
    OptionStrikeRow,
    OptionType,
    Quote,
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class Repository:
    """
    Database access layer. Encapsulates all SQL operations.

    Usage:
        repo = Repository()
        repo.save_option_chain_snapshot(snapshot)
        chain = repo.get_latest_option_chain("NIFTY", expiry_date)
    """

    def __init__(self, session: Optional[Session] = None):
        self._session = session

    @property
    def session(self) -> Session:
        if self._session is None:
            self._session = get_session()
        return self._session

    def close(self):
        if self._session:
            self._session.close()
            self._session = None

    # -----------------------------------------------------------------
    # Underlyings
    # -----------------------------------------------------------------

    def upsert_underlying(
        self,
        symbol: str,
        name: str,
        exchange: str = "NSE",
        instrument_type: str = "INDEX",
        lot_size: int = 1,
        tick_size: float = 0.05,
    ) -> None:
        """Insert or update an underlying instrument."""
        existing = self.session.query(UnderlyingDB).filter_by(symbol=symbol).first()
        if existing:
            existing.name = name
            existing.lot_size = lot_size
            existing.tick_size = tick_size
        else:
            self.session.add(UnderlyingDB(
                symbol=symbol, name=name, exchange=exchange,
                instrument_type=instrument_type, lot_size=lot_size,
                tick_size=tick_size,
            ))
        self.session.commit()

    def get_underlyings(self, enabled_only: bool = True) -> list[dict]:
        """Get all underlyings as dicts."""
        query = self.session.query(UnderlyingDB)
        if enabled_only:
            query = query.filter(UnderlyingDB.enabled == 1)
        return [
            {"symbol": u.symbol, "name": u.name, "exchange": u.exchange,
             "instrument_type": u.instrument_type, "lot_size": u.lot_size}
            for u in query.all()
        ]

    # -----------------------------------------------------------------
    # Equity Prices
    # -----------------------------------------------------------------

    def save_equity_prices(self, symbol: str, df: pd.DataFrame, source: str) -> int:
        """
        Save OHLCV DataFrame to equity_prices table.
        Skips duplicates (same symbol + date + source).
        Returns number of new rows inserted.
        """
        if df.empty:
            return 0

        inserted = 0
        for _, row in df.iterrows():
            row_date = row["date"] if isinstance(row["date"], date) else row["date"].date()
            exists = self.session.query(EquityPriceDB).filter_by(
                symbol=symbol, date=row_date, source=source
            ).first()
            if not exists:
                self.session.add(EquityPriceDB(
                    symbol=symbol,
                    date=row_date,
                    open=row.get("open"),
                    high=row.get("high"),
                    low=row.get("low"),
                    close=row.get("close"),
                    volume=row.get("volume"),
                    adjusted_close=row.get("adjusted_close"),
                    source=source,
                ))
                inserted += 1
        self.session.commit()
        return inserted

    def get_equity_history(
        self, symbol: str, start: Optional[date] = None, end: Optional[date] = None
    ) -> pd.DataFrame:
        """Get equity OHLCV history as a DataFrame."""
        query = self.session.query(EquityPriceDB).filter_by(symbol=symbol)
        if start:
            query = query.filter(EquityPriceDB.date >= start)
        if end:
            query = query.filter(EquityPriceDB.date <= end)
        query = query.order_by(EquityPriceDB.date)

        rows = query.all()
        if not rows:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])

        return pd.DataFrame([
            {"date": r.date, "open": r.open, "high": r.high,
             "low": r.low, "close": r.close, "volume": r.volume}
            for r in rows
        ])

    # -----------------------------------------------------------------
    # Options Contracts (static)
    # -----------------------------------------------------------------

    def get_or_create_contract(
        self,
        underlying: str,
        option_type: str,
        strike_price: float,
        expiry_date: date,
        lot_size: int = 1,
        instrument_type: str = "INDEX_OPTION",
        exchange: str = "NSE",
        contract_symbol: Optional[str] = None,
    ) -> int:
        """Get existing contract ID or create a new one. Returns contract ID."""
        existing = self.session.query(OptionsContractDB).filter_by(
            underlying=underlying,
            option_type=option_type,
            strike_price=strike_price,
            expiry_date=expiry_date,
        ).first()

        if existing:
            return existing.id

        contract = OptionsContractDB(
            underlying=underlying,
            exchange=exchange,
            instrument_type=instrument_type,
            option_type=option_type,
            strike_price=strike_price,
            expiry_date=expiry_date,
            contract_symbol=contract_symbol,
            lot_size=lot_size,
        )
        self.session.add(contract)
        self.session.flush()  # Get the ID without committing
        return contract.id

    # -----------------------------------------------------------------
    # Options Quotes (timestamped observations)
    # -----------------------------------------------------------------

    def save_option_quotes(
        self,
        quotes: list[OptionQuote],
        underlying: str,
        lot_size: int = 1,
    ) -> int:
        """Save a batch of option quotes. Returns count saved."""
        saved = 0
        for q in quotes:
            contract_id = self.get_or_create_contract(
                underlying=underlying,
                option_type=q.option_type.value,
                strike_price=q.strike_price,
                expiry_date=q.expiry_date,
                lot_size=lot_size,
            )
            self.session.add(OptionsQuoteDB(
                contract_id=contract_id,
                timestamp=q.timestamp,
                last_price=q.last_price,
                bid_price=q.bid_price,
                ask_price=q.ask_price,
                volume=q.volume,
                open_interest=q.open_interest,
                change_in_oi=q.change_in_oi,
                implied_volatility_source=q.implied_volatility,
                bid_ask_spread=q.bid_ask_spread,
                bid_ask_spread_pct=q.bid_ask_spread_pct,
                volume_oi_ratio=q.volume_oi_ratio,
                source=q.source,
                data_quality=q.data_quality.value,
            ))
            saved += 1
        self.session.commit()
        return saved

    # -----------------------------------------------------------------
    # Options Chain Snapshots
    # -----------------------------------------------------------------

    def save_chain_snapshot(self, snapshot: OptionChainSnapshot) -> int:
        """Save a full option chain snapshot. Returns snapshot DB id."""
        # Serialize the full snapshot to JSON for replay/audit
        snapshot_json = json.loads(snapshot.model_dump_json())

        db_snapshot = OptionsChainSnapshotDB(
            underlying=snapshot.underlying,
            expiry_date=snapshot.expiry_date,
            timestamp=snapshot.timestamp,
            spot_price=snapshot.spot_price,
            total_ce_oi=snapshot.total_ce_oi,
            total_pe_oi=snapshot.total_pe_oi,
            total_ce_volume=snapshot.total_ce_volume,
            total_pe_volume=snapshot.total_pe_volume,
            atm_strike=snapshot.atm_strike,
            snapshot_data=snapshot_json,
            source=snapshot.source,
            data_quality=snapshot.data_quality.value,
        )
        self.session.add(db_snapshot)
        self.session.commit()

        # Also save individual quotes
        all_quotes = []
        underlying_config = None
        try:
            from src.utils.config import get_config
            underlying_config = get_config().get_underlying(snapshot.underlying)
        except Exception:
            pass
        lot_size = underlying_config.get("lot_size", 1) if underlying_config else 1

        for row in snapshot.strikes:
            if row.ce:
                all_quotes.append(row.ce)
            if row.pe:
                all_quotes.append(row.pe)

        if all_quotes:
            self.save_option_quotes(all_quotes, snapshot.underlying, lot_size)

        return db_snapshot.id

    def get_latest_chain_snapshot(
        self, underlying: str, expiry_date: Optional[date] = None
    ) -> Optional[dict]:
        """
        Get the most recent chain snapshot metadata.
        Returns dict with id, timestamp, spot_price, etc. or None.
        """
        query = self.session.query(OptionsChainSnapshotDB).filter_by(underlying=underlying)
        if expiry_date:
            query = query.filter_by(expiry_date=expiry_date)
        result = query.order_by(desc(OptionsChainSnapshotDB.timestamp)).first()

        if not result:
            return None

        return {
            "id": result.id,
            "underlying": result.underlying,
            "expiry_date": result.expiry_date,
            "timestamp": result.timestamp,
            "spot_price": result.spot_price,
            "total_ce_oi": result.total_ce_oi,
            "total_pe_oi": result.total_pe_oi,
            "source": result.source,
            "data_quality": result.data_quality,
            "snapshot_data": result.snapshot_data,
        }

    # -----------------------------------------------------------------
    # Data Quality Logs
    # -----------------------------------------------------------------

    def log_data_quality(
        self,
        provider: str,
        operation: str,
        symbol: Optional[str] = None,
        total_records: int = 0,
        valid_records: int = 0,
        partial_records: int = 0,
        suspect_records: int = 0,
        missing_fields: Optional[dict] = None,
        errors: Optional[list] = None,
        overall_quality: str = "GOOD",
        duration_seconds: Optional[float] = None,
    ) -> None:
        """Log a data quality report to the database."""
        self.session.add(DataQualityLogDB(
            provider=provider,
            operation=operation,
            symbol=symbol,
            total_records=total_records,
            valid_records=valid_records,
            partial_records=partial_records,
            suspect_records=suspect_records,
            missing_fields=missing_fields or {},
            errors=errors or [],
            overall_quality=overall_quality,
            duration_seconds=duration_seconds,
        ))
        self.session.commit()

    # -----------------------------------------------------------------
    # Technical Features
    # -----------------------------------------------------------------

    def save_technical_features(self, features: TechnicalFeatures) -> int:
        """Save a TechnicalFeatures model record to DB."""
        patterns_json = [p.model_dump(mode="json") for p in features.patterns]
        db_obj = TechnicalFeatureDB(
            symbol=features.symbol,
            timestamp=features.timestamp,
            timeframe=features.timeframe.value if isinstance(features.timeframe, TimeFrame) else str(features.timeframe),
            close=features.close,
            sma_20=features.sma_20,
            sma_50=features.sma_50,
            sma_200=features.sma_200,
            ema_12=features.ema_12,
            ema_26=features.ema_26,
            rsi_14=features.rsi_14,
            macd=features.macd,
            macd_signal=features.macd_signal,
            macd_hist=features.macd_hist,
            atr_14=features.atr_14,
            adx_14=features.adx_14,
            bb_upper=features.bb_upper,
            bb_middle=features.bb_middle,
            bb_lower=features.bb_lower,
            returns_1d=features.returns_1d,
            returns_5d=features.returns_5d,
            returns_20d=features.returns_20d,
            price_to_sma20=features.price_to_sma20,
            price_to_sma50=features.price_to_sma50,
            price_to_sma200=features.price_to_sma200,
            trend_strength=features.trend_strength,
            momentum=features.momentum,
            realized_vol_5d=features.realized_vol_5d,
            realized_vol_10d=features.realized_vol_10d,
            realized_vol_20d=features.realized_vol_20d,
            realized_vol_30d=features.realized_vol_30d,
            realized_vol_60d=features.realized_vol_60d,
            volume=features.volume,
            volume_ratio_5d=features.volume_ratio_5d,
            volume_ratio_20d=features.volume_ratio_20d,
            patterns=patterns_json,
            source=features.source,
            data_quality=features.data_quality.value if hasattr(features.data_quality, "value") else str(features.data_quality),
        )
        self.session.merge(db_obj)  # Handle upsert via uq_tech_features
        self.session.commit()
        return db_obj.id

    def get_latest_technical_features(self, symbol: str, timeframe: str = "1d") -> Optional[TechnicalFeatureDB]:
        """Fetch latest technical feature record for symbol and timeframe."""
        return self.session.query(TechnicalFeatureDB).filter_by(
            symbol=symbol, timeframe=timeframe
        ).order_by(desc(TechnicalFeatureDB.timestamp)).first()

    # -----------------------------------------------------------------
    # Market Regime
    # -----------------------------------------------------------------

    def save_market_regime(self, regime: MarketRegimeResult) -> int:
        """Save a MarketRegimeResult model record to DB."""
        db_obj = MarketRegimeDB(
            symbol=regime.symbol,
            timestamp=regime.timestamp,
            regime=regime.regime.value if isinstance(regime.regime, MarketRegimeType) else str(regime.regime),
            confidence=regime.confidence,
            supporting_evidence=regime.supporting_evidence,
            conflicting_evidence=regime.conflicting_evidence,
            invalidation_conditions=regime.invalidation_conditions,
            vix_value=regime.vix_value,
            nifty_trend=regime.nifty_trend,
            banknifty_trend=regime.banknifty_trend,
            breadth_ratio=regime.breadth_ratio,
            source=regime.source,
            data_quality=regime.data_quality.value if hasattr(regime.data_quality, "value") else str(regime.data_quality),
        )
        self.session.add(db_obj)
        self.session.commit()
        return db_obj.id

    def get_latest_market_regime(self, symbol: str = "NIFTY") -> Optional[MarketRegimeDB]:
        """Fetch latest market regime record for symbol."""
        return self.session.query(MarketRegimeDB).filter_by(
            symbol=symbol
        ).order_by(desc(MarketRegimeDB.timestamp)).first()

    # -----------------------------------------------------------------
    # Options Greeks & Implied Volatility (Timestamped Observations)
    # -----------------------------------------------------------------

    def save_greeks_observation(self, obs: GreeksObservation) -> int:
        """Save a GreeksObservation to DB."""
        contract_id = self.get_or_create_contract(
            underlying=obs.underlying,
            option_type=obs.option_type.value if hasattr(obs.option_type, "value") else str(obs.option_type),
            strike_price=obs.strike_price,
            expiry_date=obs.expiry_date,
        )
        db_obj = OptionsGreeksDB(
            contract_id=contract_id,
            timestamp=obs.timestamp,
            spot_price=obs.spot_price,
            delta=obs.delta,
            gamma=obs.gamma,
            theta=obs.theta,
            vega=obs.vega,
            rho=obs.rho,
            pricing_model=obs.pricing_model,
            iv_used=obs.iv_used,
            risk_free_rate=obs.risk_free_rate,
            source=obs.source,
            data_quality=obs.data_quality.value if hasattr(obs.data_quality, "value") else str(obs.data_quality),
        )
        self.session.add(db_obj)
        self.session.commit()
        return db_obj.id

    def save_iv_observation(self, obs: ImpliedVolatilityObs) -> int:
        """Save an ImpliedVolatilityObs to DB."""
        contract_id = self.get_or_create_contract(
            underlying=obs.underlying,
            option_type=obs.option_type.value if hasattr(obs.option_type, "value") else str(obs.option_type),
            strike_price=obs.strike_price,
            expiry_date=obs.expiry_date,
        )
        db_obj = ImpliedVolatilityDB(
            contract_id=contract_id,
            timestamp=obs.timestamp,
            spot_price=obs.spot_price,
            iv=obs.iv,
            solver_method=obs.solver_method,
            solver_converged=1 if obs.solver_converged else 0,
            solver_iterations=obs.solver_iterations,
            market_price_used=obs.market_price_used,
            risk_free_rate=obs.risk_free_rate,
            source=obs.source,
            data_quality=obs.data_quality.value if hasattr(obs.data_quality, "value") else str(obs.data_quality),
        )
        self.session.add(db_obj)
        self.session.commit()
        return db_obj.id


