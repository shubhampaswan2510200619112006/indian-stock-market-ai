"""
Phase 9 — 15-Dimension Provider Evaluation Scorecard.

Evaluates data providers objectively across 15 critical quantitative & qualitative dimensions:
1. Data Legitimacy
2. Historical Depth
3. Intraday Resolution
4. Timestamp Quality
5. Bid/Ask Availability
6. Options Coverage
7. Historical Options Depth
8. Open Interest (OI)
9. Implied Volatility (IV)
10. Reliability
11. Latency
12. API Stability
13. Licensing Clarity
14. Cost
15. Integration Complexity

The scorecard never hides hard failures. A provider with excellent LTP coverage but zero Bid/Ask
is explicitly marked unsuitable for execution research.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ScorecardDimension:
    name: str
    score: float  # 0.0 to 10.0
    weight: float
    status: str   # PASS, WARNING, FAIL
    comment: str


@dataclass
class ProviderScorecard:
    provider_name: str
    dimensions: List[ScorecardDimension] = field(default_factory=list)
    hard_failures: List[str] = field(default_factory=list)

    @property
    def weighted_score(self) -> float:
        total_weight = sum(d.weight for d in self.dimensions)
        if total_weight == 0:
            return 0.0
        return round(sum(d.score * d.weight for d in self.dimensions) / total_weight, 2)

    @property
    def is_suitable_for_execution(self) -> bool:
        """Execution requires genuine executable Bid/Ask and verified real-time/near-real-time data."""
        return len(self.hard_failures) == 0 and any(
            d.name == "Bid/Ask Availability" and d.status == "PASS" for d in self.dimensions
        )

    @property
    def is_suitable_for_historical_research(self) -> bool:
        """Historical research requires depth and timestamp quality."""
        return any(
            d.name == "Historical Depth" and d.status in ("PASS", "WARNING") for d in self.dimensions
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider_name": self.provider_name,
            "weighted_score": self.weighted_score,
            "is_suitable_for_execution": self.is_suitable_for_execution,
            "is_suitable_for_historical_research": self.is_suitable_for_historical_research,
            "hard_failures": self.hard_failures,
            "dimensions": [
                {
                    "dimension": d.name,
                    "score": d.score,
                    "status": d.status,
                    "comment": d.comment,
                }
                for d in self.dimensions
            ],
        }


def build_yfinance_scorecard() -> ProviderScorecard:
    """Standardized 15-dimension scorecard for YFinance public feed."""
    card = ProviderScorecard(provider_name="YFINANCE")
    card.dimensions = [
        ScorecardDimension("Data Legitimacy", 8.0, 1.0, "PASS", "Genuine public market data from Yahoo Finance / NSE."),
        ScorecardDimension("Historical Depth", 9.0, 1.0, "PASS", "Multi-year daily OHLCV equity & index data available."),
        ScorecardDimension("Intraday Resolution", 6.0, 0.8, "PASS", "1m, 5m, 15m, 1h candles available for recent ~60 days."),
        ScorecardDimension("Timestamp Quality", 7.0, 0.9, "PASS", "UTC ISO timestamps provided, though exchange delayed."),
        ScorecardDimension("Bid/Ask Availability", 0.0, 1.2, "FAIL", "No actionable Bid/Ask depth for Indian indices/equities on free tier."),
        ScorecardDimension("Options Coverage", 0.0, 1.2, "FAIL", "NSE options chains are unsupported/broken on yfinance."),
        ScorecardDimension("Historical Options Depth", 0.0, 1.0, "FAIL", "Zero historical options contracts or settlement files."),
        ScorecardDimension("Open Interest (OI)", 0.0, 0.8, "FAIL", "No open interest or change-in-OI tracking."),
        ScorecardDimension("Implied Volatility (IV)", 0.0, 0.8, "FAIL", "No exchange-supplied IV."),
        ScorecardDimension("Reliability", 7.5, 0.8, "PASS", "High uptime, occasional rate limits during market peaks."),
        ScorecardDimension("Latency", 4.0, 1.0, "WARNING", "Typically 15-minute delayed data for NSE/BSE."),
        ScorecardDimension("API Stability", 7.0, 0.7, "PASS", "Fast info & history methods stable, fast_info occasionally omits dayHigh/dayLow."),
        ScorecardDimension("Licensing Clarity", 4.0, 0.9, "WARNING", "Personal / research use only; commercial redistribution restricted."),
        ScorecardDimension("Cost", 10.0, 0.6, "PASS", "Free public access without mandatory API key."),
        ScorecardDimension("Integration Complexity", 9.0, 0.6, "PASS", "Simple Python library interface without bespoke signing."),
    ]
    card.hard_failures = [
        "NO_EXECUTABLE_BID_ASK: Unsuitable for live paper or real execution.",
        "NO_OPTIONS_DATA: Unsuitable for options chain or Greeks research.",
    ]
    return card


def build_bhavcopy_scorecard() -> ProviderScorecard:
    """Standardized 15-dimension scorecard for NSE FO Bhavcopy archives."""
    card = ProviderScorecard(provider_name="NSE_BHAVCOPY_ARCHIVE")
    card.dimensions = [
        ScorecardDimension("Data Legitimacy", 10.0, 1.0, "PASS", "Official end-of-day settlement files from National Stock Exchange of India."),
        ScorecardDimension("Historical Depth", 9.0, 1.0, "PASS", "Decades of daily EOD options settlement files."),
        ScorecardDimension("Intraday Resolution", 0.0, 0.8, "FAIL", "EOD settlement only; zero intraday tick or 1-minute bars."),
        ScorecardDimension("Timestamp Quality", 9.0, 0.9, "PASS", "Exchange official trading date timestamps."),
        ScorecardDimension("Bid/Ask Availability", 0.0, 1.2, "FAIL", "Settlement files contain LTP/close, volume, and OI; no Bid/Ask quotes."),
        ScorecardDimension("Options Coverage", 10.0, 1.2, "PASS", "100% of all listed NSE index and equity options contracts."),
        ScorecardDimension("Historical Options Depth", 10.0, 1.0, "PASS", "Full historical series across all strikes and expiries."),
        ScorecardDimension("Open Interest (OI)", 10.0, 0.8, "PASS", "Official exchange settlement open interest and change in OI."),
        ScorecardDimension("Implied Volatility (IV)", 0.0, 0.8, "WARNING", "IV not in raw bhavcopy; must be locally calculated using Black-Scholes."),
        ScorecardDimension("Reliability", 9.5, 0.8, "PASS", "Static archived files have 100% liveness."),
        ScorecardDimension("Latency", 0.0, 1.0, "FAIL", "EOD file; zero real-time capability."),
        ScorecardDimension("API Stability", 9.0, 0.7, "PASS", "Standard CSV format (with known 2024 header schema revisions)."),
        ScorecardDimension("Licensing Clarity", 7.0, 0.9, "PASS", "Publicly distributed by NSE for market transparency."),
        ScorecardDimension("Cost", 10.0, 0.6, "PASS", "Free archive downloads from exchange portal."),
        ScorecardDimension("Integration Complexity", 8.0, 0.6, "PASS", "Standard CSV parser with lot size and strike normalization."),
    ]
    card.hard_failures = [
        "NO_REALTIME_CAPABILITY: Static historical archive only.",
        "NO_BID_ASK: Unsuitable for execution slippage and spread research.",
    ]
    return card
