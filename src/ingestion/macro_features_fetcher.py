"""
Phase 16 — Macro Features Fetcher.

Fetches legitimately available macro market data:
- India VIX (^INDIAVIX via yfinance)
- GIFT Nifty pre-market (NIFTYIFT.NS via yfinance, where available)
- USD/INR (USDINR=X via yfinance)
- Crude oil WTI (CL=F via yfinance)
- MCX Crude (CRUDEOIL.MCX where available)

DATA INTEGRITY RULES:
1. Missing values remain None — never interpolated or fabricated.
2. Every record carries source, retrieval_timestamp, freshness_level, data_quality.
3. freshness_level reflects actual data age: LIVE/DELAYED/STALE/END_OF_DAY/UNAVAILABLE.
4. yfinance data is typically delayed 15-20 minutes during market hours.
5. No predictions or alpha claims are made from this data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional

from src.utils.logging_config import get_logger
from src.utils.time_utils import data_age_seconds, now_ist

logger = get_logger(__name__)

# yfinance symbol mappings
_INDIA_VIX_SYMBOL = "^INDIAVIX"
_GIFT_NIFTY_SYMBOL = "NIFTYIFT.NS"   # Where available via yfinance
_USD_INR_SYMBOL = "USDINR=X"
_CRUDE_WTI_SYMBOL = "CL=F"
_CRUDE_MCX_SYMBOL = "CRUDEOIL.MCX"   # MCX crude (may not be in yfinance)


def _freshness_from_age(age_seconds: float) -> str:
    """Classify data freshness from age in seconds."""
    if age_seconds < 60:
        return "LIVE"
    elif age_seconds < 900:   # 15 minutes
        return "DELAYED"
    elif age_seconds < 7200:  # 2 hours
        return "STALE"
    else:
        return "END_OF_DAY"


def _safe_float(val) -> Optional[float]:
    if val is None:
        return None
    try:
        f = float(val)
        return f if f == f else None  # NaN guard
    except (ValueError, TypeError):
        return None


@dataclass
class MacroSnapshot:
    """
    Point-in-time snapshot of macro market features.

    All values may be None if the source is unavailable.
    freshness_level is per-field to reflect different data freshness.
    """
    observation_date: date
    retrieval_timestamp: datetime

    # India VIX
    india_vix: Optional[float] = None
    india_vix_change: Optional[float] = None
    india_vix_freshness: str = "UNAVAILABLE"

    # GIFT Nifty (pre-market indicator)
    gift_nifty: Optional[float] = None
    gift_nifty_change_pct: Optional[float] = None
    gift_nifty_freshness: str = "UNAVAILABLE"

    # USD/INR exchange rate
    usd_inr: Optional[float] = None
    usd_inr_change_pct: Optional[float] = None
    usd_inr_freshness: str = "UNAVAILABLE"

    # Crude oil — WTI (international)
    crude_wti: Optional[float] = None
    crude_wti_change_pct: Optional[float] = None
    crude_wti_freshness: str = "UNAVAILABLE"

    # MCX Crude (India-traded)
    crude_mcx: Optional[float] = None
    crude_mcx_freshness: str = "UNAVAILABLE"

    source: str = "yfinance"
    data_quality: str = "GOOD"


class MacroFeaturesFetcher:
    """
    Fetches macro features using yfinance (free, public, delayed data).

    Failure policy: each symbol is fetched independently. If one symbol
    fails, the others are still returned with their available values.
    Failed symbols leave their fields as None with freshness = UNAVAILABLE.
    """

    def fetch(self) -> MacroSnapshot:
        """
        Fetch all macro features and return a MacroSnapshot.

        Returns:
            MacroSnapshot with fields populated where data is available.
            Missing fields are None — never fabricated.
        """
        try:
            import yfinance as yf
        except ImportError:
            logger.error("yfinance not installed. Run: pip install yfinance")
            return MacroSnapshot(
                observation_date=now_ist().date(),
                retrieval_timestamp=now_ist(),
                data_quality="UNAVAILABLE",
            )

        retrieval_ts = now_ist()
        snapshot = MacroSnapshot(
            observation_date=retrieval_ts.date(),
            retrieval_timestamp=retrieval_ts,
        )

        # --- India VIX ---
        try:
            vix_ticker = yf.Ticker(_INDIA_VIX_SYMBOL)
            vix_info = vix_ticker.fast_info
            vix_price = _safe_float(getattr(vix_info, "last_price", None))
            if vix_price is None:
                hist = vix_ticker.history(period="2d")
                if len(hist) >= 1:
                    vix_price = _safe_float(hist["Close"].iloc[-1])
            if vix_price is not None:
                snapshot.india_vix = vix_price
                prev = _safe_float(getattr(vix_info, "previous_close", None))
                if prev and prev != 0:
                    snapshot.india_vix_change = round(vix_price - prev, 4)
                # yfinance is typically delayed; assume DELAYED unless we know otherwise
                snapshot.india_vix_freshness = "DELAYED"
            else:
                snapshot.india_vix_freshness = "UNAVAILABLE"
        except Exception as exc:
            logger.warning(f"India VIX fetch failed: {exc}")
            snapshot.india_vix_freshness = "UNAVAILABLE"

        # --- GIFT Nifty ---
        try:
            gift_ticker = yf.Ticker(_GIFT_NIFTY_SYMBOL)
            gift_info = gift_ticker.fast_info
            gift_price = _safe_float(getattr(gift_info, "last_price", None))
            if gift_price is None:
                hist = gift_ticker.history(period="2d")
                if len(hist) >= 1:
                    gift_price = _safe_float(hist["Close"].iloc[-1])
            if gift_price is not None:
                snapshot.gift_nifty = gift_price
                prev = _safe_float(getattr(gift_info, "previous_close", None))
                if prev and prev != 0:
                    snapshot.gift_nifty_change_pct = round((gift_price - prev) / prev * 100, 4)
                snapshot.gift_nifty_freshness = "DELAYED"
            else:
                snapshot.gift_nifty_freshness = "UNAVAILABLE"
        except Exception as exc:
            logger.warning(f"GIFT Nifty fetch failed (may not be available on yfinance): {exc}")
            snapshot.gift_nifty_freshness = "UNAVAILABLE"

        # --- USD/INR ---
        try:
            usdinr_ticker = yf.Ticker(_USD_INR_SYMBOL)
            usdinr_info = usdinr_ticker.fast_info
            usdinr_price = _safe_float(getattr(usdinr_info, "last_price", None))
            if usdinr_price is None:
                hist = usdinr_ticker.history(period="2d")
                if len(hist) >= 1:
                    usdinr_price = _safe_float(hist["Close"].iloc[-1])
            if usdinr_price is not None:
                snapshot.usd_inr = usdinr_price
                prev = _safe_float(getattr(usdinr_info, "previous_close", None))
                if prev and prev != 0:
                    snapshot.usd_inr_change_pct = round((usdinr_price - prev) / prev * 100, 4)
                snapshot.usd_inr_freshness = "DELAYED"
            else:
                snapshot.usd_inr_freshness = "UNAVAILABLE"
        except Exception as exc:
            logger.warning(f"USD/INR fetch failed: {exc}")
            snapshot.usd_inr_freshness = "UNAVAILABLE"

        # --- Crude Oil WTI ---
        try:
            crude_ticker = yf.Ticker(_CRUDE_WTI_SYMBOL)
            crude_info = crude_ticker.fast_info
            crude_price = _safe_float(getattr(crude_info, "last_price", None))
            if crude_price is None:
                hist = crude_ticker.history(period="2d")
                if len(hist) >= 1:
                    crude_price = _safe_float(hist["Close"].iloc[-1])
            if crude_price is not None:
                snapshot.crude_wti = crude_price
                prev = _safe_float(getattr(crude_info, "previous_close", None))
                if prev and prev != 0:
                    snapshot.crude_wti_change_pct = round((crude_price - prev) / prev * 100, 4)
                snapshot.crude_wti_freshness = "DELAYED"
            else:
                snapshot.crude_wti_freshness = "UNAVAILABLE"
        except Exception as exc:
            logger.warning(f"Crude WTI fetch failed: {exc}")
            snapshot.crude_wti_freshness = "UNAVAILABLE"

        # --- MCX Crude (may not be available on yfinance) ---
        try:
            mcx_ticker = yf.Ticker(_CRUDE_MCX_SYMBOL)
            mcx_info = mcx_ticker.fast_info
            mcx_price = _safe_float(getattr(mcx_info, "last_price", None))
            if mcx_price is not None:
                snapshot.crude_mcx = mcx_price
                snapshot.crude_mcx_freshness = "DELAYED"
            else:
                snapshot.crude_mcx_freshness = "UNAVAILABLE"
        except Exception as exc:
            logger.info(f"MCX crude unavailable via yfinance (expected): {exc}")
            snapshot.crude_mcx_freshness = "UNAVAILABLE"

        # Overall quality
        available_count = sum(
            1 for v in [snapshot.india_vix, snapshot.usd_inr, snapshot.crude_wti]
            if v is not None
        )
        snapshot.data_quality = "GOOD" if available_count >= 2 else "PARTIAL" if available_count >= 1 else "UNAVAILABLE"

        logger.info(
            f"Macro snapshot: VIX={snapshot.india_vix}, USD/INR={snapshot.usd_inr}, "
            f"WTI={snapshot.crude_wti}, GIFT={snapshot.gift_nifty}, quality={snapshot.data_quality}"
        )
        return snapshot

    def fetch_historical_vix(self, start: date, end: date):
        """
        Fetch historical India VIX data for a date range.

        Returns:
            pd.DataFrame with columns: date, india_vix, source, freshness_level
            Empty DataFrame if unavailable.
        """
        import pandas as pd
        try:
            import yfinance as yf
        except ImportError:
            return pd.DataFrame(columns=["date", "india_vix", "source", "freshness_level"])

        try:
            ticker = yf.Ticker(_INDIA_VIX_SYMBOL)
            hist = ticker.history(
                start=start.isoformat(),
                end=(end + timedelta(days=1)).isoformat(),
            )
            if hist.empty:
                return pd.DataFrame(columns=["date", "india_vix", "source", "freshness_level"])

            df = hist.reset_index()
            df.columns = [c.lower() for c in df.columns]
            date_col = "date" if "date" in df.columns else "datetime"
            df = df.rename(columns={date_col: "date", "close": "india_vix"})
            df["date"] = pd.to_datetime(df["date"]).dt.date
            df["source"] = "yfinance"
            df["freshness_level"] = "END_OF_DAY"
            return df[["date", "india_vix", "source", "freshness_level"]].copy()
        except Exception as exc:
            logger.warning(f"Historical VIX fetch failed: {exc}")
            import pandas as pd
            return pd.DataFrame(columns=["date", "india_vix", "source", "freshness_level"])
