"""
Canonical Research Registry.

Single authoritative registry of research modules and preregistered hypotheses.
Fields per Phase 10 specification:
- research_id
- research_name
- required_data
- minimum_history
- execution_requirement
- status
- reason_if_blocked
- provenance
- research_type
- confirmation_status
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ResearchItem:
    research_id: str
    research_name: str
    required_data: str  # e.g., intraday_5m, cross_sectional_equities, historical_options_bid_ask
    minimum_history: str
    execution_requirement: str  # NONE, STATISTICAL_FRICTION, REALISTIC_BID_ASK
    status: str  # READY, BLOCKED, HISTORICAL_FROZEN, REJECTED, INSUFFICIENT_DATA
    reason_if_blocked: Optional[str]
    provenance: Dict[str, Any]
    research_type: str  # EXPLORATORY, CONFIRMATORY
    confirmation_status: str  # UNTESTED, REJECTED, INSUFFICIENT_DATA, FROZEN

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ResearchRegistry:
    """
    Registry maintaining all historical and valid future research tracks.
    """

    def __init__(self):
        self._items: Dict[str, ResearchItem] = {}
        self._initialize_canonical_registry()

    def _initialize_canonical_registry(self) -> None:
        """Loads canonical Phase 9.8 hypotheses and future research templates."""
        canonical_items = [
            ResearchItem(
                research_id="P98-H001",
                research_name="15m Opening Range Breakout",
                required_data="intraday_5m",
                minimum_history=">=60 sessions (Exploratory) / >=250 sessions (Confirmatory)",
                execution_requirement="STATISTICAL_FRICTION",
                status="INSUFFICIENT_DATA",
                reason_if_blocked="Preregistered sample criterion (N>=60) not met (observed N=59)",
                provenance={"phase": "Phase 9.8 / 9.9 Frozen Baseline", "track": "Track A"},
                research_type="EXPLORATORY",
                confirmation_status="INSUFFICIENT_DATA",
            ),
            ResearchItem(
                research_id="P98-H002",
                research_name="Overnight Gap 30m Mean-Reversion",
                required_data="intraday_5m",
                minimum_history=">=60 sessions",
                execution_requirement="STATISTICAL_FRICTION",
                status="INSUFFICIENT_DATA",
                reason_if_blocked="Preregistered sample criterion not met (observed N=19)",
                provenance={"phase": "Phase 9.8 / 9.9 Frozen Baseline", "track": "Track A"},
                research_type="EXPLORATORY",
                confirmation_status="INSUFFICIENT_DATA",
            ),
            ResearchItem(
                research_id="P98-H003",
                research_name="30m Return Momentum",
                required_data="intraday_5m",
                minimum_history=">=60 sessions",
                execution_requirement="STATISTICAL_FRICTION",
                status="REJECTED",
                reason_if_blocked="Microstructure friction exceeds gross returns (-10.8 bps net exp)",
                provenance={"phase": "Phase 9.8 / 9.9 Frozen Baseline", "track": "Track B"},
                research_type="EXPLORATORY",
                confirmation_status="REJECTED",
            ),
            ResearchItem(
                research_id="P98-H004",
                research_name="Volatility Compression Breakout",
                required_data="intraday_5m",
                minimum_history=">=60 sessions",
                execution_requirement="STATISTICAL_FRICTION",
                status="REJECTED",
                reason_if_blocked="Microstructure friction exceeds gross returns (-9.8 bps net exp)",
                provenance={"phase": "Phase 9.8 / 9.9 Frozen Baseline", "track": "Track C"},
                research_type="EXPLORATORY",
                confirmation_status="REJECTED",
            ),
            ResearchItem(
                research_id="P98-H005",
                research_name="RBI MPC Policy Drift (3-day)",
                required_data="daily_index",
                minimum_history=">=10 events",
                execution_requirement="STATISTICAL_FRICTION",
                status="REJECTED",
                reason_if_blocked="Gross edge decayed after statutory costs (-49.2 bps net exp)",
                provenance={"phase": "Phase 9.8 / 9.9 Frozen Baseline", "track": "Track D"},
                research_type="CONFIRMATORY",
                confirmation_status="REJECTED",
            ),
            ResearchItem(
                research_id="P98-H006",
                research_name="20D Relative Strength Spread",
                required_data="cross_sectional_equities",
                minimum_history=">=250 sessions across constituents",
                execution_requirement="STATISTICAL_FRICTION",
                status="REJECTED",
                reason_if_blocked="Survivorship bias risk and turnover friction (-48.4 bps net exp)",
                provenance={"phase": "Phase 9.8 / 9.9 Frozen Baseline", "track": "Track E"},
                research_type="CONFIRMATORY",
                confirmation_status="REJECTED",
            ),
            ResearchItem(
                research_id="P98-H007",
                research_name="Macro Regime Uncertainty Calibration",
                required_data="daily_index",
                minimum_history=">=250 sessions",
                execution_requirement="NONE",
                status="REJECTED",
                reason_if_blocked="Brier score improvement (<5%) failed significance threshold",
                provenance={"phase": "Phase 9.8 / 9.9 Frozen Baseline", "track": "Track F"},
                research_type="CONFIRMATORY",
                confirmation_status="REJECTED",
            ),
            ResearchItem(
                research_id="P98-H008",
                research_name="Options Historical Quote Boundary Audit",
                required_data="historical_options_bid_ask",
                minimum_history=">=10,000 quotes",
                execution_requirement="REALISTIC_BID_ASK",
                status="INSUFFICIENT_DATA",
                reason_if_blocked="0 genuine paired Bid/Ask quotes; options execution backtest BLOCKED",
                provenance={"phase": "Phase 9.8 / 9.9 Frozen Baseline", "track": "Track G"},
                research_type="CONFIRMATORY",
                confirmation_status="INSUFFICIENT_DATA",
            ),
            # Ready Future Research Template for Cross-Sectional Equity:
            ResearchItem(
                research_id="TMPL-CS-001",
                research_name="Cross-Sectional Factor Dispersion (Template)",
                required_data="cross_sectional_equities",
                minimum_history=">=250 sessions",
                execution_requirement="STATISTICAL_FRICTION",
                status="READY",
                reason_if_blocked=None,
                provenance={"source": "Platform Cross-Sectional Foundation", "track": "Cross-Sectional"},
                research_type="EXPLORATORY",
                confirmation_status="UNTESTED",
            ),
        ]

        for item in canonical_items:
            self._items[item.research_id] = item

    def get_item(self, research_id: str) -> Optional[ResearchItem]:
        return self._items.get(research_id)

    def all_items(self) -> List[ResearchItem]:
        return list(self._items.values())

    def to_dict(self) -> Dict[str, Any]:
        return {k: v.to_dict() for k, v in self._items.items()}
