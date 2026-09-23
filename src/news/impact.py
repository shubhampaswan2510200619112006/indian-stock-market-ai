"""
News Market Impact Analyzer (Phase 7).
Correlates news timestamps against price return, volume ratio, IV, and OI shifts.
STRICT RULE: Uses non-causal language. Stores ImpactObservation without claiming causality.
"""

from typing import Dict, Optional
from src.news.models import ImpactObservation


class NewsImpactAnalyzer:
    """Correlates headline timestamps with market movement using non-causal language."""

    @staticmethod
    def correlate_market_impact(
        article_id: str,
        symbol: str,
        price_return_after: float = 0.0,
        volume_ratio: float = 1.0,
        iv_change: float = 0.0,
        oi_change: float = 0.0,
    ) -> ImpactObservation:
        """
        Creates a non-causal ImpactObservation record.
        """
        notes = (
            f"Observed price return ({price_return_after * 100:.2f}%) and volume ratio ({volume_ratio:.1f}x) "
            f"following news publication. Causal attribution is uncertain."
        )

        return ImpactObservation(
            article_id=article_id,
            symbol=symbol,
            observed_price_return=price_return_after,
            observed_volume_ratio=volume_ratio,
            observed_iv_change=iv_change,
            observed_oi_change=oi_change,
            observation_notes=notes,
        )
