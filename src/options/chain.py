"""
Option Chain Analyzer.

Takes a raw OptionChainSnapshot and produces OptionChainAnalysis with:
- Per-strike classification (ATM/ITM/OTM, liquidity, spreads)
- Chain-level analytics (PCR, max pain, OI zones, unusual activity)
- ALL interpretations use PROBABILISTIC language
- Clear DATA UNAVAILABLE flags where fields are null

This is the core Phase 1 analysis engine.
"""

from __future__ import annotations

import statistics
from datetime import datetime
from typing import Optional

import numpy as np

from src.ingestion.schemas import (
    DataQualityStatus,
    Moneyness,
    OIConcentrationZone,
    OptionChainAnalysis,
    OptionChainSnapshot,
    OptionQuote,
    OptionStrikeRow,
    OptionType,
    UnusualActivity,
)
from src.options.utils import (
    calculate_max_pain,
    classify_moneyness,
    distance_from_atm,
    distance_from_atm_pct,
    find_atm_strike,
)
from src.utils.config import get_config
from src.utils.logging_config import get_logger
from src.utils.time_utils import now_ist

logger = get_logger(__name__)


class OptionChainAnalyzer:
    """
    Analyzes an option chain snapshot and produces structured analytics.

    All interpretations are probabilistic — never deterministic claims.
    Missing data is flagged, never invented.
    """

    def __init__(self):
        config = get_config()
        oc_config = config.option_chain_config
        self._high_oi_percentile = oc_config.get("high_oi_percentile", 90)
        self._unusual_volume_sigma = oc_config.get("unusual_volume_sigma", 2.0)
        self._wide_spread_pct = oc_config.get("wide_spread_threshold_pct", 5.0)
        self._min_volume = oc_config.get("min_volume_for_analysis", 10)
        self._min_oi = oc_config.get("min_oi_for_analysis", 100)

    def analyze(self, snapshot: OptionChainSnapshot) -> OptionChainAnalysis:
        """
        Run full analysis on an option chain snapshot.

        Returns OptionChainAnalysis with all metrics and probabilistic interpretations.
        """
        if not snapshot.strikes:
            return OptionChainAnalysis(
                underlying=snapshot.underlying,
                expiry_date=snapshot.expiry_date,
                spot_price=snapshot.spot_price,
                timestamp=snapshot.timestamp,
                source=snapshot.source,
                data_quality=DataQualityStatus.UNAVAILABLE,
                chain_interpretation="No option chain data available for analysis.",
            )

        # Step 1: Classify moneyness for each strike
        classified = self._classify_strikes(snapshot)

        # Step 2: Chain-level aggregates
        total_ce_oi, total_pe_oi = self._sum_oi(classified)
        total_ce_vol, total_pe_vol = self._sum_volume(classified)

        # Step 3: PCR
        pcr_oi = (total_pe_oi / total_ce_oi) if total_ce_oi and total_ce_oi > 0 else None
        pcr_vol = (total_pe_vol / total_ce_vol) if total_ce_vol and total_ce_vol > 0 else None

        # Step 4: Max Pain
        max_pain = calculate_max_pain(snapshot)

        # Step 5: ATM strike and ATM IV
        atm_strike = snapshot.atm_strike or find_atm_strike(
            snapshot.spot_price, [r.strike_price for r in classified]
        )
        atm_iv_ce, atm_iv_pe = self._get_atm_iv(classified, atm_strike)

        # Step 6: OI concentration zones
        oi_zones = self._find_oi_concentration(classified, snapshot.spot_price)

        # Step 7: Unusual activity
        unusual = self._detect_unusual_activity(classified)

        # Step 8: Liquidity warnings
        liquidity_warnings = self._check_liquidity(classified)

        # Step 9: Generate probabilistic interpretation
        interpretation = self._generate_interpretation(
            snapshot.underlying, snapshot.spot_price, pcr_oi, pcr_vol,
            max_pain, oi_zones, atm_iv_ce, atm_iv_pe, unusual,
        )

        return OptionChainAnalysis(
            underlying=snapshot.underlying,
            expiry_date=snapshot.expiry_date,
            spot_price=snapshot.spot_price,
            put_call_ratio_oi=round(pcr_oi, 3) if pcr_oi is not None else None,
            put_call_ratio_volume=round(pcr_vol, 3) if pcr_vol is not None else None,
            max_pain_strike=max_pain,
            atm_strike=atm_strike,
            atm_iv_ce=atm_iv_ce,
            atm_iv_pe=atm_iv_pe,
            total_ce_oi=total_ce_oi,
            total_pe_oi=total_pe_oi,
            total_ce_volume=total_ce_vol,
            total_pe_volume=total_pe_vol,
            oi_concentration_zones=oi_zones,
            unusual_activity=unusual,
            liquidity_warnings=liquidity_warnings,
            chain_interpretation=interpretation,
            timestamp=snapshot.timestamp,
            source=snapshot.source,
            data_quality=snapshot.data_quality,
        )

    # -----------------------------------------------------------------
    # Private analysis methods
    # -----------------------------------------------------------------

    def _classify_strikes(self, snapshot: OptionChainSnapshot) -> list[OptionStrikeRow]:
        """Add moneyness classification to each strike row."""
        classified = []
        for row in snapshot.strikes:
            m_ce = classify_moneyness(snapshot.spot_price, row.strike_price, OptionType.CE)
            m_pe = classify_moneyness(snapshot.spot_price, row.strike_price, OptionType.PE)
            # Use CE moneyness for the row display (conventional)
            classified.append(row.model_copy(update={
                "moneyness": m_ce,
                "distance_from_atm": distance_from_atm(snapshot.spot_price, row.strike_price),
                "distance_from_atm_pct": round(
                    distance_from_atm_pct(snapshot.spot_price, row.strike_price), 2
                ),
            }))
        return classified

    def _sum_oi(self, strikes: list[OptionStrikeRow]) -> tuple[int, int]:
        """Sum total OI for calls and puts."""
        ce_oi = sum(r.ce.open_interest for r in strikes if r.ce and r.ce.open_interest)
        pe_oi = sum(r.pe.open_interest for r in strikes if r.pe and r.pe.open_interest)
        return ce_oi, pe_oi

    def _sum_volume(self, strikes: list[OptionStrikeRow]) -> tuple[int, int]:
        """Sum total volume for calls and puts."""
        ce_vol = sum(r.ce.volume for r in strikes if r.ce and r.ce.volume)
        pe_vol = sum(r.pe.volume for r in strikes if r.pe and r.pe.volume)
        return ce_vol, pe_vol

    def _get_atm_iv(
        self, strikes: list[OptionStrikeRow], atm_strike: Optional[float]
    ) -> tuple[Optional[float], Optional[float]]:
        """Get ATM implied volatility for CE and PE."""
        if not atm_strike:
            return None, None
        for row in strikes:
            if row.strike_price == atm_strike:
                ce_iv = row.ce.implied_volatility if row.ce else None
                pe_iv = row.pe.implied_volatility if row.pe else None
                return ce_iv, pe_iv
        return None, None

    def _find_oi_concentration(
        self,
        strikes: list[OptionStrikeRow],
        spot: float,
    ) -> list[OIConcentrationZone]:
        """
        Find strikes with significant OI concentration.

        Uses percentile-based thresholds to identify high-OI strikes.
        Interpretations are PROBABILISTIC — NOT "support" or "resistance".
        """
        zones = []

        # Collect all OI values for percentile calculation
        ce_ois = [r.ce.open_interest for r in strikes if r.ce and r.ce.open_interest and r.ce.open_interest >= self._min_oi]
        pe_ois = [r.pe.open_interest for r in strikes if r.pe and r.pe.open_interest and r.pe.open_interest >= self._min_oi]

        ce_threshold = _percentile(ce_ois, self._high_oi_percentile) if ce_ois else float("inf")
        pe_threshold = _percentile(pe_ois, self._high_oi_percentile) if pe_ois else float("inf")

        for row in strikes:
            # High Call OI
            if row.ce and row.ce.open_interest and row.ce.open_interest >= ce_threshold:
                position = "above" if row.strike_price > spot else "below" if row.strike_price < spot else "at"
                zones.append(OIConcentrationZone(
                    strike_price=row.strike_price,
                    option_type=OptionType.CE,
                    open_interest=row.ce.open_interest,
                    change_in_oi=row.ce.change_in_oi,
                    interpretation=(
                        f"High call OI concentration at {row.strike_price} ({position} spot). "
                        f"This may indicate potential resistance if writers are short, "
                        f"but OI interpretation is probabilistic and can be misleading."
                    ),
                ))

            # High Put OI
            if row.pe and row.pe.open_interest and row.pe.open_interest >= pe_threshold:
                position = "below" if row.strike_price < spot else "above" if row.strike_price > spot else "at"
                zones.append(OIConcentrationZone(
                    strike_price=row.strike_price,
                    option_type=OptionType.PE,
                    open_interest=row.pe.open_interest,
                    change_in_oi=row.pe.change_in_oi,
                    interpretation=(
                        f"High put OI concentration at {row.strike_price} ({position} spot). "
                        f"This may indicate potential support if writers are short, "
                        f"but OI interpretation is probabilistic and can be misleading."
                    ),
                ))

        return zones

    def _detect_unusual_activity(self, strikes: list[OptionStrikeRow]) -> list[UnusualActivity]:
        """
        Detect unusual volume or OI changes using statistical thresholds.

        A strike is flagged as unusual if its volume or OI change exceeds
        the mean + N standard deviations of the chain.
        """
        unusual = []

        # Collect all volumes and OI changes
        ce_volumes = [r.ce.volume for r in strikes if r.ce and r.ce.volume and r.ce.volume >= self._min_volume]
        pe_volumes = [r.pe.volume for r in strikes if r.pe and r.pe.volume and r.pe.volume >= self._min_volume]
        ce_oi_changes = [abs(r.ce.change_in_oi) for r in strikes if r.ce and r.ce.change_in_oi is not None]
        pe_oi_changes = [abs(r.pe.change_in_oi) for r in strikes if r.pe and r.pe.change_in_oi is not None]

        # Check CE unusual volume
        unusual.extend(
            self._check_unusual(strikes, ce_volumes, OptionType.CE, "volume", "ce")
        )
        # Check PE unusual volume
        unusual.extend(
            self._check_unusual(strikes, pe_volumes, OptionType.PE, "volume", "pe")
        )
        # Check CE unusual OI change
        unusual.extend(
            self._check_unusual(strikes, ce_oi_changes, OptionType.CE, "oi_change", "ce")
        )
        # Check PE unusual OI change
        unusual.extend(
            self._check_unusual(strikes, pe_oi_changes, OptionType.PE, "oi_change", "pe")
        )

        return unusual

    def _check_unusual(
        self,
        strikes: list[OptionStrikeRow],
        values: list[int | float],
        option_type: OptionType,
        metric: str,
        side: str,
    ) -> list[UnusualActivity]:
        """Check for unusual values using mean + σ threshold."""
        if len(values) < 5:
            return []

        avg = statistics.mean(values)
        std = statistics.stdev(values) if len(values) > 1 else 0
        threshold = avg + self._unusual_volume_sigma * std

        if threshold <= 0:
            return []

        results = []
        for row in strikes:
            quote: Optional[OptionQuote] = row.ce if side == "ce" else row.pe
            if not quote:
                continue

            val = None
            if metric == "volume" and quote.volume is not None:
                val = quote.volume
            elif metric == "oi_change" and quote.change_in_oi is not None:
                val = abs(quote.change_in_oi)

            if val is not None and val > threshold:
                results.append(UnusualActivity(
                    strike_price=row.strike_price,
                    option_type=option_type,
                    metric=metric,
                    value=float(val),
                    average=round(avg, 1),
                    std_dev=round(std, 1),
                    interpretation=(
                        f"Unusual {metric.replace('_', ' ')} of {val:,.0f} "
                        f"at {row.strike_price} {option_type.value} "
                        f"(avg: {avg:,.0f}, threshold: {threshold:,.0f}). "
                        f"This may indicate increased trader interest, "
                        f"but should be investigated further before drawing conclusions."
                    ),
                ))

        return results

    def _check_liquidity(self, strikes: list[OptionStrikeRow]) -> list[str]:
        """Flag strikes with wide bid-ask spreads or low liquidity."""
        warnings = []

        for row in strikes:
            for quote, side in [(row.ce, "CE"), (row.pe, "PE")]:
                if not quote:
                    continue
                if (
                    quote.bid_ask_spread_pct is not None
                    and quote.bid_ask_spread_pct > self._wide_spread_pct
                    and quote.volume is not None
                    and quote.volume > 0
                ):
                    warnings.append(
                        f"{row.strike_price} {side}: Wide bid-ask spread "
                        f"({quote.bid_ask_spread_pct:.1f}%). Potential liquidity concern."
                    )

        return warnings[:10]  # Limit to top 10

    def _generate_interpretation(
        self,
        underlying: str,
        spot: float,
        pcr_oi: Optional[float],
        pcr_vol: Optional[float],
        max_pain: Optional[float],
        oi_zones: list[OIConcentrationZone],
        atm_iv_ce: Optional[float],
        atm_iv_pe: Optional[float],
        unusual: list[UnusualActivity],
    ) -> str:
        """
        Generate a probabilistic chain interpretation.

        NEVER produces deterministic claims.
        NEVER says "market WILL move to X".
        """
        parts = []

        parts.append(f"{underlying} Option Chain Analysis (Spot: {spot:,.2f})")
        parts.append("")

        # PCR
        if pcr_oi is not None:
            pcr_desc = "neutral"
            if pcr_oi > 1.2:
                pcr_desc = "elevated (may suggest bullish sentiment from put writing perspective, but interpretation varies)"
            elif pcr_oi < 0.8:
                pcr_desc = "low (may suggest bearish sentiment or call-heavy positioning, but interpretation varies)"
            parts.append(f"Put/Call Ratio (OI): {pcr_oi:.3f} — {pcr_desc}")

        # Max Pain
        if max_pain is not None:
            mp_diff = max_pain - spot
            mp_pct = (mp_diff / spot) * 100 if spot > 0 else 0
            parts.append(
                f"Max Pain: {max_pain:,.2f} ({mp_pct:+.1f}% from spot). "
                f"This is a theoretical level, not a price prediction."
            )

        # ATM IV
        if atm_iv_ce is not None or atm_iv_pe is not None:
            iv_parts = []
            if atm_iv_ce is not None:
                iv_parts.append(f"CE: {atm_iv_ce:.1f}%")
            if atm_iv_pe is not None:
                iv_parts.append(f"PE: {atm_iv_pe:.1f}%")
            parts.append(f"ATM IV: {', '.join(iv_parts)}")

        # OI Zones summary
        if oi_zones:
            ce_zones = [z for z in oi_zones if z.option_type == OptionType.CE]
            pe_zones = [z for z in oi_zones if z.option_type == OptionType.PE]
            if ce_zones:
                zone_strs = [f"{z.strike_price:,.0f}" for z in ce_zones[:3]]
                parts.append(f"High Call OI zones: {', '.join(zone_strs)} (potential resistance areas)")
            if pe_zones:
                zone_strs = [f"{z.strike_price:,.0f}" for z in pe_zones[:3]]
                parts.append(f"High Put OI zones: {', '.join(zone_strs)} (potential support areas)")

        # Unusual activity
        if unusual:
            parts.append(f"Unusual activity detected at {len(unusual)} strike(s). Review individual alerts.")

        if not parts or len(parts) <= 2:
            parts.append("Insufficient data for detailed chain interpretation.")

        parts.append("")
        parts.append(
            "DISCLAIMER: Option chain analysis is probabilistic. OI-based interpretations "
            "can be misleading. High OI does not guarantee support/resistance. "
            "Always consider market regime, events, and other factors."
        )

        return "\n".join(parts)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _percentile(values: list[int | float], pct: float) -> float:
    """Calculate percentile from a list of values."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * (pct / 100.0)
    f = int(k)
    c = f + 1
    if c >= len(sorted_vals):
        return float(sorted_vals[-1])
    d = k - f
    return float(sorted_vals[f] + d * (sorted_vals[c] - sorted_vals[f]))
