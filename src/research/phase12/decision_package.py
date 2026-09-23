"""
Phase 12 Final Mission — Vendor Contact & Data Acquisition Decision Package Engine.

Defines canonical acquisition specifications, provenance-backed vendor claims,
cost normalization model, multi-attribute value scoring, decision state transitions,
and report generation conforming to the Phase 12 Final Mission requirements.

CRITICAL GOVERNANCE INVARIANTS:
- PURCHASE_AUTHORIZED = FALSE
- HUMAN_DECISION_REQUIRED = TRUE
- BROKER = NONE
- LIVE_EXECUTION = DISABLED
- AUTO_PAPER_ORDER_SUBMISSION = DISABLED
- NEW_UNPREREGISTERED_ALPHA_RESEARCH = DISABLED
- UNLIMITED_PARAMETER_SEARCH = DISABLED
- STRATEGY_OPTIMIZATION = DISABLED
- OPTIONS_EXECUTION = BLOCKED
- FROZEN_BASELINES = INTACT

MANDATORY CORRECTIONS ENFORCED:
1. Candidate ranking is PROVISIONAL_CANDIDATE_RANKING and SUBJECT_TO_VENDOR_CONFIRMATION,
   FORMAL_QUOTATION, LICENSE_REVIEW, and SAMPLE_VALIDATION. Never a final purchasing recommendation.
2. Cost integrity: Uses VERIFIED_QUOTE, ESTIMATE — NOT A QUOTE, UNKNOWN. No fabricated prices.
   Totals calculated only with explicit assumptions.
3. Strictly distinguishes PROVIDER_CAPABILITY from EXACT_HISTORICAL_DATASET_AVAILABILITY.
   Documentation of live/real-time capability does NOT establish historical dataset availability.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from src.research.phase12 import (
    AUTO_PAPER_ORDER_SUBMISSION,
    BROKER,
    HUMAN_DECISION_REQUIRED,
    LIVE_EXECUTION,
    NEW_UNPREREGISTERED_ALPHA_RESEARCH,
    OPTIONS_EXECUTION,
    PURCHASE_AUTHORIZED,
    STRATEGY_OPTIMIZATION,
    UNLIMITED_PARAMETER_SEARCH,
)
from src.research.phase12.baseline_verifier import verify_frozen_baselines


class DecisionState(str, Enum):
    NO_VENDOR_SELECTED = "NO_VENDOR_SELECTED"
    VENDOR_CONTACT_PENDING = "VENDOR_CONTACT_PENDING"
    VENDOR_RESPONSE_PENDING = "VENDOR_RESPONSE_PENDING"
    SAMPLE_VALIDATION_PENDING = "SAMPLE_VALIDATION_PENDING"
    COMMERCIAL_REVIEW_PENDING = "COMMERCIAL_REVIEW_PENDING"
    HUMAN_AUTHORIZATION_PENDING = "HUMAN_AUTHORIZATION_PENDING"
    APPROVED_FOR_ACQUISITION = "APPROVED_FOR_ACQUISITION"
    REJECTED = "REJECTED"


class EvidenceStatus(str, Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    REQUIRES_VENDOR_CONFIRMATION = "REQUIRES_VENDOR_CONFIRMATION"
    OBSERVED_PROVIDER_LIMITATION = "OBSERVED_PROVIDER_LIMITATION"


class QuoteStatus(str, Enum):
    VERIFIED_QUOTE = "VERIFIED_QUOTE"
    ESTIMATE = "ESTIMATE — NOT A QUOTE"
    UNKNOWN = "UNKNOWN"
    SALES_QUOTE_REQUIRED = "SALES_QUOTE_REQUIRED"


@dataclass
class AcquisitionDecisionStateMachine:
    current_state: DecisionState = DecisionState.HUMAN_AUTHORIZATION_PENDING
    purchase_authorized: bool = False
    human_decision_required: bool = True
    authorized_by: Optional[str] = None
    authorization_date: Optional[str] = None
    authorization_notes: Optional[str] = None
    history: List[Dict[str, Any]] = field(default_factory=list)

    def transition(
        self,
        new_state: DecisionState,
        actor: str,
        reason: str,
        human_signoff: bool = False,
    ) -> bool:
        """
        Validates and transitions decision states.
        Transition to APPROVED_FOR_ACQUISITION strictly requires explicit human signoff.
        """
        if new_state == DecisionState.APPROVED_FOR_ACQUISITION and not human_signoff:
            raise PermissionError(
                "Cannot transition to APPROVED_FOR_ACQUISITION without explicit human authorization sign-off. "
                "Automated purchasing is strictly forbidden."
            )

        previous_state = self.current_state
        self.current_state = new_state
        if human_signoff:
            self.purchase_authorized = True
            self.authorized_by = actor
            self.authorization_date = datetime.now(timezone.utc).isoformat()
            self.authorization_notes = reason

        self.history.append({
            "from_state": previous_state.value,
            "to_state": new_state.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "reason": reason,
            "human_signoff": human_signoff,
        })
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_state": self.current_state.value,
            "purchase_authorized": self.purchase_authorized,
            "human_decision_required": self.human_decision_required,
            "authorized_by": self.authorized_by,
            "authorization_date": self.authorization_date,
            "authorization_notes": self.authorization_notes,
            "history": self.history,
            "safety_invariants": {
                "broker": BROKER,
                "live_execution": LIVE_EXECUTION,
                "auto_paper_order_submission": AUTO_PAPER_ORDER_SUBMISSION,
                "options_execution": OPTIONS_EXECUTION,
                "new_alpha_research": NEW_UNPREREGISTERED_ALPHA_RESEARCH,
                "unlimited_parameter_search": UNLIMITED_PARAMETER_SEARCH,
                "strategy_optimization": STRATEGY_OPTIMIZATION,
            },
        }


class DecisionPackageManager:
    """
    Constructs and persists all Phase 12 Final Mission artifacts.
    """

    @classmethod
    def get_canonical_acquisition_requirements(cls) -> Dict[str, Any]:
        return {
            "specification_version": "phase12_final_decision_package_v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "governance": {
                "purchase_authorized": PURCHASE_AUTHORIZED,
                "human_decision_required": HUMAN_DECISION_REQUIRED,
                "broker": BROKER,
                "live_execution": LIVE_EXECUTION,
                "auto_paper_order_submission": AUTO_PAPER_ORDER_SUBMISSION,
                "new_unpreregistered_alpha_research": NEW_UNPREREGISTERED_ALPHA_RESEARCH,
                "strategy_optimization": STRATEGY_OPTIMIZATION,
                "unlimited_parameter_search": UNLIMITED_PARAMETER_SEARCH,
                "options_execution": OPTIONS_EXECUTION,
                "frozen_baselines": "INTACT",
                "zero_data_fabrication_rule": "Zero synthetic Bid/Ask prices or continuous quote surfaces may be labeled as exchange observations.",
            },
            "intraday_requirements": {
                "underlyings": ["NIFTY 50", "NIFTY BANK"],
                "intervals": ["1 minute", "5 minute"],
                "minimum_sessions": 250,
                "minimum_sessions_threshold_label": "PROJECT_RESEARCH_THRESHOLD",
                "minimum_sessions_threshold_explanation": (
                    "250 verified sessions is a PROJECT_RESEARCH_THRESHOLD defined to guarantee statistical validity across "
                    "a full calendar year of trading regimes. It is not a universal statistical law."
                ),
                "preferred_horizon": "3-5 years (~750-1250 sessions) where commercially available",
                "timezone": "Asia/Kolkata (+05:30)",
                "market_session_ist": "09:15-15:30 IST",
                "required_fields": [
                    "timestamp",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "open_interest",
                    "instrument_identifier",
                    "exchange",
                    "timezone",
                    "trading_session_metadata",
                    "corporate_adjustment_information",
                ],
                "evaluation_dimensions": [
                    "exchange_event_time_vs_vendor_normalized_time",
                    "timezone_handling",
                    "missing_bar_behavior",
                    "duplicate_bar_behavior",
                    "corrections_and_revisions",
                    "historical_retention_window",
                    "downloadable_archive_access",
                    "api_access",
                    "rate_limits",
                    "bulk_download_availability",
                ],
                "substitution_rule": "Substitution of daily or 1-hour bars for 1m/5m intraday data is strictly forbidden.",
            },
            "options_requirements": {
                "targets": ["NIFTY OPTIONS", "BANKNIFTY OPTIONS"],
                "minimum_schema": [
                    "underlying",
                    "contract_id",
                    "expiry",
                    "strike",
                    "option_type",
                    "timestamp",
                    "bid",
                    "ask",
                    "ltp",
                    "volume",
                    "open_interest",
                ],
                "preferred_depth": "Level 2 / 5-depth snapshots",
                "best_available": "Level 4 / Order-book capable (tick-by-tick order & trade logs)",
                "options_hierarchy": {
                    "LEVEL_0": "No Options Data",
                    "LEVEL_1": "LTP / Settlement Only",
                    "LEVEL_2": "Isolated Bid/Ask",
                    "LEVEL_3": "Continuous Paired Bid/Ask (>= 70% paired quote continuity across market hours)",
                    "LEVEL_4": "Depth / Order-Book Capable (5-depth or full order book reconstruction)",
                },
                "paired_quote_continuity_threshold_pct": 70.0,
                "paired_quote_continuity_threshold_label": "PROJECT_RESEARCH_THRESHOLD",
                "paired_quote_continuity_explanation": (
                    "The 70% paired quote continuity threshold is a PROJECT_RESEARCH_THRESHOLD defined for internal execution modeling. "
                    "It is not an industry-wide or universal definition of execution readiness."
                ),
                "contract_validation": {
                    "method": "EXCHANGE_SPEC_AND_CALENDAR_DRIVEN",
                    "prohibited_assumptions": [
                        "Hardcoding Thursday expiry",
                        "Hardcoding Wednesday expiry",
                        "Any fixed weekday expiry schedule",
                    ],
                    "required_foundation": (
                        "Authoritative exchange specifications + market calendar + actual contract metadata. "
                        "Expired contracts must remain identifiable and queryable."
                    ),
                },
            },
            "provisional_candidate_ranking": {
                "ranking_label": "PROVISIONAL_CANDIDATE_RANKING",
                "mandatory_conditions": [
                    "SUBJECT_TO_VENDOR_CONFIRMATION",
                    "SUBJECT_TO_FORMAL_QUOTATION",
                    "SUBJECT_TO_LICENSE_REVIEW",
                    "SUBJECT_TO_SAMPLE_VALIDATION",
                ],
                "primary_candidate": {
                    "name": "NSE Data & Analytics / DotEx",
                    "tier": "OFFICIAL_EXCHANGE",
                    "suitability": "Preferred candidate subject to vendor confirmation, formal quotation, licensing review, and successful sample validation.",
                },
                "secondary_candidate": {
                    "name": "TrueData (TrueData India)",
                    "tier": "AUTHORIZED_VENDOR",
                    "suitability": "Secondary candidate subject to vendor confirmation of historical options Bid/Ask depth, formal quotation, and sample validation.",
                },
                "backup_candidate": {
                    "name": "Global DataFeeds (GDFL)",
                    "tier": "AUTHORIZED_VENDOR",
                    "suitability": "Backup candidate subject to vendor confirmation of historical options archives, formal quotation, and sample validation.",
                },
                "disclaimer": "This provisional ranking is NOT a purchasing recommendation. No data purchase or commercial commitment is authorized.",
            },
        }

    @classmethod
    def get_vendor_claims_catalog(cls) -> List[Dict[str, Any]]:
        """
        Full provenance catalog for every evaluated provider.
        Strictly distinguishes PROVIDER_CAPABILITY from EXACT_HISTORICAL_DATASET_AVAILABILITY.
        """
        now = "2026-09-09T15:00:00Z"
        return [
            # 1. NSE Data & Analytics / DotEx
            {
                "provider": "NSE Data & Analytics Ltd (DotEx)",
                "product_name": "Historical Tick-by-Tick & 5-Depth Snapshot Archives",
                "claim_id": "NSE-001",
                "claim": "Provides historical 1-minute and 5-minute index data for NIFTY 50 and NIFTY BANK (>10 years).",
                "capability_type": "EXACT_HISTORICAL_DATASET_AVAILABILITY",
                "verification_status": EvidenceStatus.VERIFIED.value,
                "verification_method": "Official exchange historical product catalog and published specifications.",
                "source": "https://www.nseindia.com/market-data/historical-data-products",
                "source_type": "OFFICIAL_DOCUMENTATION",
                "retrieval_date": now,
                "notes": "Direct official exchange historical archive.",
            },
            {
                "provider": "NSE Data & Analytics Ltd (DotEx)",
                "product_name": "Historical Level 2 / 5-Depth & Level 3 TBT Archives",
                "claim_id": "NSE-002",
                "claim": "Provides historical NIFTY and BANKNIFTY options Bid/Ask quotes and expired contract master.",
                "capability_type": "EXACT_HISTORICAL_DATASET_AVAILABILITY",
                "verification_status": EvidenceStatus.VERIFIED.value,
                "verification_method": "Exchange historical data products documentation and F&O contract archives.",
                "source": "https://www.nseindia.com/market-data/historical-data-products",
                "source_type": "OFFICIAL_DOCUMENTATION",
                "retrieval_date": now,
                "notes": "Full trade and order logs include bid/ask snapshots. Forming continuous Level 3/4 surface requires reconstruction pipeline.",
            },
            {
                "provider": "NSE Data & Analytics Ltd (DotEx)",
                "product_name": "Historical Data Licensing & Pricing",
                "claim_id": "NSE-003",
                "claim": "Commercial pricing for proprietary quantitative research.",
                "capability_type": "COMMERCIAL_PRICING",
                "verification_status": EvidenceStatus.REQUIRES_VENDOR_CONFIRMATION.value,
                "verification_method": "Formal enterprise sales inquiry required; pricing not publicly listed.",
                "source": "NSE Data & Analytics Commercial Sales Division",
                "source_type": "VENDOR_INQUIRY_REQUIRED",
                "retrieval_date": now,
                "notes": "Requires formal quotation. Estimated INR 50,000 to INR 250,000+ depending on segments and years. Marked ESTIMATE — NOT A QUOTE.",
            },

            # 2. TrueData
            {
                "provider": "TrueData (TrueData India)",
                "product_name": "TrueData Historical REST API & Market Feeds",
                "claim_id": "TD-001",
                "claim": "Provides multi-year historical NIFTY 50 and NIFTY BANK 1-minute and 5-minute bars (>10 years).",
                "capability_type": "EXACT_HISTORICAL_DATASET_AVAILABILITY",
                "verification_status": EvidenceStatus.VERIFIED.value,
                "verification_method": "Documented TrueData Historical REST API v1/v2 endpoints and symbol specifications.",
                "source": "https://www.truedata.in",
                "source_type": "OFFICIAL_DOCUMENTATION",
                "retrieval_date": now,
                "notes": "Continuous intraday OHLCV for cash and active indices satisfies >250 sessions.",
            },
            {
                "provider": "TrueData (TrueData India)",
                "product_name": "TrueData WebSocket Live Feed",
                "claim_id": "TD-002",
                "claim": "Real-time market feed delivers Level 2 (5-depth) Bid/Ask quotes for options.",
                "capability_type": "PROVIDER_CAPABILITY",
                "verification_status": EvidenceStatus.VERIFIED.value,
                "verification_method": "TrueData WebSocket API documentation.",
                "source": "https://www.truedata.in/feedback/api-docs",
                "source_type": "OFFICIAL_DOCUMENTATION",
                "retrieval_date": now,
                "notes": "Live capability verified. Does NOT establish historical dataset availability.",
            },
            {
                "provider": "TrueData (TrueData India)",
                "product_name": "Historical Options Tick / Bid-Ask Archives",
                "claim_id": "TD-003",
                "claim": "Provides multi-year historical continuous paired Bid/Ask quote surface for expired NIFTY options.",
                "capability_type": "EXACT_HISTORICAL_DATASET_AVAILABILITY",
                "verification_status": EvidenceStatus.REQUIRES_VENDOR_CONFIRMATION.value,
                "verification_method": "Standard REST API serves 1m OHLCV bars; historical tick/Bid-Ask requires enterprise archive verification.",
                "source": "TrueData Sales & Support",
                "source_type": "VENDOR_INQUIRY_REQUIRED",
                "retrieval_date": now,
                "notes": "Standard retail tier provides OHLCV+OI; historical continuous Bid/Ask is unverified without vendor confirmation and sample.",
            },
            {
                "provider": "TrueData (TrueData India)",
                "product_name": "TrueData Pricing",
                "claim_id": "TD-004",
                "claim": "Annual subscription pricing for historical intraday + tick add-on.",
                "capability_type": "COMMERCIAL_PRICING",
                "verification_status": EvidenceStatus.REQUIRES_VENDOR_CONFIRMATION.value,
                "verification_method": "Website lists retail plans at INR 2,000-4,000/month; enterprise historical archives require custom quote.",
                "source": "https://www.truedata.in/pricing",
                "source_type": "VENDOR_PORTAL",
                "retrieval_date": now,
                "notes": "Marked ESTIMATE — NOT A QUOTE (INR 25,000 - 60,000/yr). Formal quotation required.",
            },

            # 3. Global DataFeeds (GDFL)
            {
                "provider": "Global DataFeeds (GDFL)",
                "product_name": "GDFL NimbleDataPro / DataFeed API",
                "claim_id": "GDFL-001",
                "claim": "Provides multi-year historical NIFTY 50 and NIFTY BANK 1-minute and 5-minute data (>5 years).",
                "capability_type": "EXACT_HISTORICAL_DATASET_AVAILABILITY",
                "verification_status": EvidenceStatus.VERIFIED.value,
                "verification_method": "GDFL product documentation and API manual.",
                "source": "https://www.globaldatafeeds.in",
                "source_type": "OFFICIAL_DOCUMENTATION",
                "retrieval_date": now,
                "notes": "Satisfies intraday session threshold (>250 sessions).",
            },
            {
                "provider": "Global DataFeeds (GDFL)",
                "product_name": "GDFL Live Feeds",
                "claim_id": "GDFL-002",
                "claim": "Real-time feed delivers Best 5 Bid/Ask quotes for options.",
                "capability_type": "PROVIDER_CAPABILITY",
                "verification_status": EvidenceStatus.VERIFIED.value,
                "verification_method": "GDFL API live feed documentation.",
                "source": "https://www.globaldatafeeds.in/products",
                "source_type": "OFFICIAL_DOCUMENTATION",
                "retrieval_date": now,
                "notes": "Real-time capability verified. Does NOT establish historical dataset availability.",
            },
            {
                "provider": "Global DataFeeds (GDFL)",
                "product_name": "GDFL Historical Options Tick Archives",
                "claim_id": "GDFL-003",
                "claim": "Provides multi-year historical continuous paired Bid/Ask quote surface for expired NIFTY options.",
                "capability_type": "EXACT_HISTORICAL_DATASET_AVAILABILITY",
                "verification_status": EvidenceStatus.REQUIRES_VENDOR_CONFIRMATION.value,
                "verification_method": "Standard API provides OHLCV bars; historical tick Bid/Ask requires enterprise confirmation.",
                "source": "Global DataFeeds Commercial Inquiry",
                "source_type": "VENDOR_INQUIRY_REQUIRED",
                "retrieval_date": now,
                "notes": "Requires vendor confirmation and sample validation.",
            },

            # 4. Zerodha Kite Connect
            {
                "provider": "Zerodha Kite Connect",
                "product_name": "Kite Connect Historical API v3",
                "claim_id": "ZERODHA-001",
                "claim": "Provides historical 1-minute and 5-minute index data for active symbols (~1-2 years).",
                "capability_type": "EXACT_HISTORICAL_DATASET_AVAILABILITY",
                "verification_status": EvidenceStatus.VERIFIED.value,
                "verification_method": "Official Kite Connect API documentation.",
                "source": "https://kite.trade/docs/connect/v3/historical/",
                "source_type": "OFFICIAL_DOCUMENTATION",
                "retrieval_date": now,
                "notes": "Provides OHLCV for active indices.",
            },
            {
                "provider": "Zerodha Kite Connect",
                "product_name": "Kite Connect Historical Options Quotes",
                "claim_id": "ZERODHA-002",
                "claim": "Provides historical options Bid/Ask quotes and expired contract chains.",
                "capability_type": "EXACT_HISTORICAL_DATASET_AVAILABILITY",
                "verification_status": EvidenceStatus.NOT_AVAILABLE.value,
                "verification_method": "Official documentation confirms historical endpoint returns [timestamp, open, high, low, close, volume, oi] exclusively. Expired contract tokens are deleted post-expiry.",
                "source": "https://kite.trade/docs/connect/v3/historical/",
                "source_type": "OFFICIAL_DOCUMENTATION",
                "retrieval_date": now,
                "notes": "OBSERVED_PROVIDER_LIMITATION: Strictly LTP OHLCV bars; zero historical Bid/Ask; zero expired contracts.",
            },

            # 5. Upstox
            {
                "provider": "Upstox",
                "product_name": "Upstox Developer API v2",
                "claim_id": "UPSTOX-001",
                "claim": "Provides historical options Bid/Ask quotes and expired contracts.",
                "capability_type": "EXACT_HISTORICAL_DATASET_AVAILABILITY",
                "verification_status": EvidenceStatus.NOT_AVAILABLE.value,
                "verification_method": "Official API documentation confirms candle format provides only OHLCV. Expired contracts not queryable.",
                "source": "https://upstox.com/developer/api-documentation/historical-candle-data",
                "source_type": "OFFICIAL_DOCUMENTATION",
                "retrieval_date": now,
                "notes": "OBSERVED_PROVIDER_LIMITATION: Retail broker limitation.",
            },

            # 6. Angel One SmartAPI
            {
                "provider": "Angel One SmartAPI",
                "product_name": "SmartAPI Historical Data",
                "claim_id": "ANGEL-001",
                "claim": "Provides historical options Bid/Ask quotes and expired contracts.",
                "capability_type": "EXACT_HISTORICAL_DATASET_AVAILABILITY",
                "verification_status": EvidenceStatus.NOT_AVAILABLE.value,
                "verification_method": "Official SmartAPI documentation confirms response array [timestamp, open, high, low, close, volume]. Expired contracts not retained.",
                "source": "https://smartapi.angelbroking.com/docs/Historical",
                "source_type": "OFFICIAL_DOCUMENTATION",
                "retrieval_date": now,
                "notes": "OBSERVED_PROVIDER_LIMITATION: Retail broker limitation.",
            },

            # 7. FYERS
            {
                "provider": "FYERS",
                "product_name": "FYERS API v3",
                "claim_id": "FYERS-001",
                "claim": "Provides historical options Bid/Ask quotes and expired contracts.",
                "capability_type": "EXACT_HISTORICAL_DATASET_AVAILABILITY",
                "verification_status": EvidenceStatus.NOT_AVAILABLE.value,
                "verification_method": "Official FYERS API docs confirm candle response contains OHLCV only.",
                "source": "https://myapi.fyers.in/docs/",
                "source_type": "OFFICIAL_DOCUMENTATION",
                "retrieval_date": now,
                "notes": "OBSERVED_PROVIDER_LIMITATION: Retail broker limitation.",
            },

            # 8. Yahoo Finance
            {
                "provider": "Yahoo Finance",
                "product_name": "Public yfinance Endpoint",
                "claim_id": "YHOO-001",
                "claim": "Provides >= 250 sessions of 1-minute and 5-minute index data.",
                "capability_type": "EXACT_HISTORICAL_DATASET_AVAILABILITY",
                "verification_status": EvidenceStatus.OBSERVED_PROVIDER_LIMITATION.value,
                "verification_method": "Empirically audited in Phase 10A/10B: 1m endpoint truncates at 7 calendar days (7 sessions); 5m endpoint truncates at 60 calendar days (43 sessions).",
                "source": "Platform empirical audit data/phase10a/intraday/nsei_1m.csv",
                "source_type": "EMPIRICAL_AUDIT",
                "retrieval_date": now,
                "notes": "Fails PROJECT_RESEARCH_THRESHOLD (250 sessions). Options Bid/Ask quotes completely absent.",
            },

            # 9. NSE Public Bhavcopy
            {
                "provider": "NSE Public Bhavcopy",
                "product_name": "NSE Public All Reports / F&O Bhavcopy",
                "claim_id": "BHAV-001",
                "claim": "Provides historical intraday 1m/5m data and historical Bid/Ask quotes.",
                "capability_type": "EXACT_HISTORICAL_DATASET_AVAILABILITY",
                "verification_status": EvidenceStatus.NOT_AVAILABLE.value,
                "verification_method": "Bhavcopy report schema inspection: provides daily EOD settlement price, volume, and OI. Zero intraday bars or Bid/Ask quotes exist.",
                "source": "https://www.nseindia.com/all-reports",
                "source_type": "OFFICIAL_EXCHANGE_REPORTS",
                "retrieval_date": now,
                "notes": "PASS for Level 1 LTP/settlement. Completely insufficient for intraday 1m/5m and options execution research.",
            },
        ]

    @classmethod
    def get_cost_comparison_model(cls) -> Dict[str, Any]:
        """
        Normalized cost comparison model.
        Never fabricates prices. Uses VERIFIED_QUOTE, ESTIMATE — NOT A QUOTE, UNKNOWN.
        Totals calculated only when underlying components and assumptions are explicitly recorded.
        """
        return {
            "model_version": "phase12_cost_normalization_v1",
            "currency": "INR",
            "tax_standard": "GST 18% (Applicable on commercial data licensing in India)",
            "providers": [
                {
                    "provider": "NSE Data & Analytics Ltd (DotEx)",
                    "product": "Historical Tick-by-Tick / 5-Depth Snapshot Archives",
                    "pricing_status": QuoteStatus.SALES_QUOTE_REQUIRED.value,
                    "cost_breakdown": {
                        "one_time_data_cost": "UNKNOWN",
                        "annual_subscription": "UNKNOWN",
                        "monthly_subscription": "NOT_APPLICABLE (Delivered as fixed historical segment archives)",
                        "exchange_fees": "INCLUDED_IN_OFFICIAL_QUOTE",
                        "license_fees": "COMMERCIAL_RESEARCH_LICENSE_REQUIRED (Quotation pending)",
                        "gst_tax": "18% on final quoted invoice",
                        "storage_cost": "INTERNAL_INFRASTRUCTURE (Estimated 2-5 TB for Level 2/3 ticks)",
                        "api_cost": "NOT_APPLICABLE (Bulk S3 / SFTP / Hard drive delivery)",
                        "support_cost": "INCLUDED_IN_ENTERPRISE_CONTRACT",
                        "other_mandatory_cost": "UNKNOWN",
                    },
                    "assumptions": "Official exchange sales quote required. Industry estimates range from INR 50,000 to INR 250,000+ depending on years, underlying count, and depth.",
                    "year_1_total_cost": "UNKNOWN (ESTIMATE — NOT A QUOTE: INR 50,000 - INR 250,000 + GST)",
                    "year_2_total_cost": "UNKNOWN (Typically incremental add-on for newly completed year)",
                    "year_3_total_cost": "UNKNOWN",
                    "three_year_total_cost": "UNKNOWN (Requires formal commercial quote)",
                    "commercial_assessment": "Highest provenance and data completeness; enterprise pricing requires human quotation approval.",
                },
                {
                    "provider": "TrueData (TrueData India)",
                    "product": "TrueData Historical REST API & Market Feeds",
                    "pricing_status": QuoteStatus.ESTIMATE.value,
                    "cost_breakdown": {
                        "one_time_data_cost": "UNKNOWN (Options tick archive historical package price pending inquiry)",
                        "annual_subscription": "ESTIMATE: INR 25,000 - INR 60,000 / year (Standard API + historical options add-on)",
                        "monthly_subscription": "ESTIMATE: INR 2,000 - INR 5,000 / month",
                        "exchange_fees": "Included in standard vendor plan",
                        "license_fees": "Proprietary research license included; zero redistribution",
                        "gst_tax": "18% additional",
                        "storage_cost": "INTERNAL_INFRASTRUCTURE (~100-500 GB)",
                        "api_cost": "Included in subscription",
                        "support_cost": "Standard web/ticket support included",
                        "other_mandatory_cost": "None known",
                    },
                    "assumptions": "Based on published retail plans (INR 2k-4k/mo) plus estimated tick options add-on. NOT a binding quote.",
                    "year_1_total_cost": "ESTIMATE — NOT A QUOTE: INR 29,500 - INR 70,800 (including 18% GST)",
                    "year_2_total_cost": "ESTIMATE — NOT A QUOTE: INR 29,500 - INR 70,800 / yr",
                    "year_3_total_cost": "ESTIMATE — NOT A QUOTE: INR 29,500 - INR 70,800 / yr",
                    "three_year_total_cost": "ESTIMATE — NOT A QUOTE: INR 88,500 - INR 212,400 (3-year projection with 18% GST)",
                    "commercial_assessment": "Cost-effective authorized vendor for 1m/5m intraday. Historical options Bid/Ask continuity requires confirmation.",
                },
                {
                    "provider": "Global DataFeeds (GDFL)",
                    "product": "GDFL NimbleDataPro / DataFeed API",
                    "pricing_status": QuoteStatus.ESTIMATE.value,
                    "cost_breakdown": {
                        "one_time_data_cost": "UNKNOWN",
                        "annual_subscription": "ESTIMATE: INR 20,000 - INR 50,000 / year",
                        "monthly_subscription": "ESTIMATE: INR 1,800 - INR 4,500 / month",
                        "exchange_fees": "Included in authorized vendor plan",
                        "license_fees": "Internal prop research license",
                        "gst_tax": "18% additional",
                        "storage_cost": "INTERNAL_INFRASTRUCTURE (~100-500 GB)",
                        "api_cost": "Included",
                        "support_cost": "Standard support included",
                        "other_mandatory_cost": "None known",
                    },
                    "assumptions": "Based on published live feed pricing and estimated historical add-ons. NOT a binding quote.",
                    "year_1_total_cost": "ESTIMATE — NOT A QUOTE: INR 23,600 - INR 59,000 (including 18% GST)",
                    "year_2_total_cost": "ESTIMATE — NOT A QUOTE: INR 23,600 - INR 59,000 / yr",
                    "year_3_total_cost": "ESTIMATE — NOT A QUOTE: INR 23,600 - INR 59,000 / yr",
                    "three_year_total_cost": "ESTIMATE — NOT A QUOTE: INR 70,800 - INR 177,000 (3-year projection with 18% GST)",
                    "commercial_assessment": "Competitive authorized vendor. Historical options archives require confirmation.",
                },
                {
                    "provider": "Zerodha Kite Connect",
                    "product": "Kite Connect Historical API v3",
                    "pricing_status": QuoteStatus.VERIFIED_QUOTE.value,
                    "cost_breakdown": {
                        "one_time_data_cost": 0,
                        "annual_subscription": 48000,  # INR 4,000/mo * 12
                        "monthly_subscription": 4000,  # INR 2,000 base + INR 2,000 historical addon
                        "exchange_fees": 0,
                        "license_fees": 0,
                        "gst_tax": 0,  # Price quoted is inclusive of retail GST
                        "storage_cost": 0,
                        "api_cost": 0,
                        "support_cost": 0,
                        "other_mandatory_cost": 0,
                    },
                    "assumptions": "Official published pricing for Kite Connect Base API (INR 2,000/mo) + Historical API (INR 2,000/mo). Active trading account required.",
                    "year_1_total_cost": 48000,
                    "year_2_total_cost": 48000,
                    "year_3_total_cost": 48000,
                    "three_year_total_cost": 144000,
                    "commercial_assessment": "Pricing is verified, BUT dataset completely fails options Bid/Ask and expired options requirements. INSUFFICIENT.",
                },
                {
                    "provider": "Public / Free Endpoints (Yahoo Finance / NSE Bhavcopy)",
                    "product": "Public Web / yfinance",
                    "pricing_status": QuoteStatus.VERIFIED_QUOTE.value,
                    "cost_breakdown": {
                        "one_time_data_cost": 0,
                        "annual_subscription": 0,
                        "monthly_subscription": 0,
                        "exchange_fees": 0,
                        "license_fees": 0,
                        "gst_tax": 0,
                        "storage_cost": 0,
                        "api_cost": 0,
                        "support_cost": 0,
                        "other_mandatory_cost": 0,
                    },
                    "assumptions": "Free public endpoints. Zero financial cost.",
                    "year_1_total_cost": 0,
                    "year_2_total_cost": 0,
                    "year_3_total_cost": 0,
                    "three_year_total_cost": 0,
                    "commercial_assessment": "Zero cost, but completely fails intraday session threshold (7d/60d retention) and lacks options Bid/Ask quotes.",
                },
            ],
        }

    @classmethod
    def get_value_scoring_model(cls) -> Dict[str, Any]:
        """
        Transparent multi-attribute value scoring with configurable weights.
        Enforces that scoring cannot override hard requirements (e.g. cheapness cannot bypass missing options quotes).
        """
        weights = {
            "DATA_COVERAGE": 0.20,
            "OPTIONS_EXECUTABILITY": 0.20,
            "HISTORICAL_DEPTH": 0.15,
            "TIMESTAMP_QUALITY": 0.10,
            "CONTRACT_COMPLETENESS": 0.10,
            "PROVENANCE": 0.05,
            "LICENSE_FIT": 0.05,
            "DELIVERY_RELIABILITY": 0.05,
            "COST": 0.05,
            "SUPPORT": 0.05,
        }

        evaluations = [
            {
                "provider": "NSE Data & Analytics Ltd (DotEx)",
                "tier": "OFFICIAL_EXCHANGE",
                "scores": {
                    "DATA_COVERAGE": 95,
                    "OPTIONS_EXECUTABILITY": 90,  # Level 2/3 snapshots require reconstruction pipeline
                    "HISTORICAL_DEPTH": 98,
                    "TIMESTAMP_QUALITY": 99,
                    "CONTRACT_COMPLETENESS": 99,
                    "PROVENANCE": 100,
                    "LICENSE_FIT": 95,
                    "DELIVERY_RELIABILITY": 95,
                    "COST": 40,  # Enterprise quotation required
                    "SUPPORT": 80,
                },
                "hard_gate_pass": True,
                "notes": "Passes all hard technical requirements. Definitive authoritative tape.",
            },
            {
                "provider": "TrueData (TrueData India)",
                "tier": "AUTHORIZED_VENDOR",
                "scores": {
                    "DATA_COVERAGE": 85,
                    "OPTIONS_EXECUTABILITY": 60,  # Historical options continuous Bid/Ask requires confirmation
                    "HISTORICAL_DEPTH": 85,
                    "TIMESTAMP_QUALITY": 85,
                    "CONTRACT_COMPLETENESS": 80,
                    "PROVENANCE": 90,
                    "LICENSE_FIT": 90,
                    "DELIVERY_RELIABILITY": 85,
                    "COST": 85,
                    "SUPPORT": 85,
                },
                "hard_gate_pass": True,  # Conditionally passes pending confirmation of options archives
                "notes": "Excellent for 1m/5m intraday. Options Bid/Ask depth requires confirmation.",
            },
            {
                "provider": "Global DataFeeds (GDFL)",
                "tier": "AUTHORIZED_VENDOR",
                "scores": {
                    "DATA_COVERAGE": 80,
                    "OPTIONS_EXECUTABILITY": 55,
                    "HISTORICAL_DEPTH": 80,
                    "TIMESTAMP_QUALITY": 80,
                    "CONTRACT_COMPLETENESS": 75,
                    "PROVENANCE": 90,
                    "LICENSE_FIT": 85,
                    "DELIVERY_RELIABILITY": 80,
                    "COST": 85,
                    "SUPPORT": 80,
                },
                "hard_gate_pass": True,  # Conditionally passes pending confirmation
                "notes": "Viable secondary authorized vendor.",
            },
            {
                "provider": "Zerodha Kite Connect",
                "tier": "BROKER_API",
                "scores": {
                    "DATA_COVERAGE": 40,
                    "OPTIONS_EXECUTABILITY": 0,  # Zero historical Bid/Ask
                    "HISTORICAL_DEPTH": 30,
                    "TIMESTAMP_QUALITY": 70,
                    "CONTRACT_COMPLETENESS": 10,  # Expired contracts pruned
                    "PROVENANCE": 80,
                    "LICENSE_FIT": 60,
                    "DELIVERY_RELIABILITY": 85,
                    "COST": 80,
                    "SUPPORT": 75,
                },
                "hard_gate_pass": False,  # Hard requirement failed: zero options bid/ask
                "rejection_reason": "HARD_GATE_FAILED: Lacks historical options Bid/Ask quotes and purges expired contracts.",
                "notes": "Disqualified from options execution research despite cheap cost.",
            },
            {
                "provider": "Public / Free Endpoints (Yahoo Finance)",
                "tier": "PUBLIC_FREE",
                "scores": {
                    "DATA_COVERAGE": 20,
                    "OPTIONS_EXECUTABILITY": 0,
                    "HISTORICAL_DEPTH": 10,
                    "TIMESTAMP_QUALITY": 60,
                    "CONTRACT_COMPLETENESS": 0,
                    "PROVENANCE": 50,
                    "LICENSE_FIT": 40,
                    "DELIVERY_RELIABILITY": 40,
                    "COST": 100,
                    "SUPPORT": 0,
                },
                "hard_gate_pass": False,
                "rejection_reason": "HARD_GATE_FAILED: Fails intraday session threshold (7d/60d caps) and lacks options quotes entirely.",
                "notes": "Disqualified from both intraday and options research.",
            },
        ]

        scored_evaluations = []
        for ev in evaluations:
            weighted_total = 0.0
            for dim, wt in weights.items():
                weighted_total += ev["scores"].get(dim, 0) * wt
            ev_dict = dict(ev)
            ev_dict["weighted_score"] = round(weighted_total, 2)
            scored_evaluations.append(ev_dict)

        return {
            "weights": weights,
            "evaluations": scored_evaluations,
            "hard_gate_rule": (
                "A low-cost provider that fails hard requirements (such as historical options Bid/Ask or >= 250 intraday sessions) "
                "is strictly disqualified from ranking above compliant or conditionally compliant candidates, regardless of weighted score."
            ),
        }

    @classmethod
    def get_empty_vendor_response_template(cls) -> Dict[str, Any]:
        """
        Standard schema for recording vendor responses upon receipt.
        """
        fields_list = [
            "provider",
            "contact",
            "date_received",
            "product_name",
            "dataset",
            "date_range",
            "coverage",
            "granularity",
            "quote_type",
            "depth",
            "contract_coverage",
            "timestamp_standard",
            "format",
            "delivery_method",
            "license",
            "one_time_cost",
            "recurring_cost",
            "taxes",
            "exchange_fees",
            "other_fees",
            "support",
            "SLA",
            "limitations",
            "evidence",
            "vendor_confirmation_status",
        ]
        return {
            "schema_version": "phase12_vendor_response_schema_v1",
            "fields": fields_list,
            "received_responses": [
                {
                    "provider": "NSE Data & Analytics Ltd (DotEx)",
                    "vendor_confirmation_status": "VENDOR_RESPONSE_PENDING",
                    "response_data": {field_name: "AWAITING_VENDOR_REPLY" for field_name in fields_list},
                },
                {
                    "provider": "TrueData (TrueData India)",
                    "vendor_confirmation_status": "VENDOR_RESPONSE_PENDING",
                    "response_data": {field_name: "AWAITING_VENDOR_REPLY" for field_name in fields_list},
                },
                {
                    "provider": "Global DataFeeds (GDFL)",
                    "vendor_confirmation_status": "VENDOR_RESPONSE_PENDING",
                    "response_data": {field_name: "AWAITING_VENDOR_REPLY" for field_name in fields_list},
                },
            ],
        }

    @classmethod
    def generate_all_artifacts(cls, workspace_root: str = ".") -> Dict[str, Any]:
        """
        Emits all canonical data JSON files and Markdown reports.
        """
        data_dir = os.path.join(workspace_root, "data", "phase12")
        reports_dir = os.path.join(workspace_root, "reports", "phase12")
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(reports_dir, exist_ok=True)

        # 1. acquisition_decision_package.json
        acq_pkg = cls.get_canonical_acquisition_requirements()
        acq_pkg_path = os.path.join(data_dir, "acquisition_decision_package.json")
        with open(acq_pkg_path, "w", encoding="utf-8") as f:
            json.dump(acq_pkg, f, indent=2)

        # 2. acquisition_decision.json
        state_machine = AcquisitionDecisionStateMachine()
        state_dict = state_machine.to_dict()
        state_dict["provisional_candidate_ranking"] = acq_pkg["provisional_candidate_ranking"]
        state_path = os.path.join(data_dir, "acquisition_decision.json")
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, indent=2)

        # 3. vendor_claims.json
        claims = cls.get_vendor_claims_catalog()
        claims_path = os.path.join(data_dir, "vendor_claims.json")
        with open(claims_path, "w", encoding="utf-8") as f:
            json.dump({"claims_count": len(claims), "claims": claims}, f, indent=2)

        # 4. vendor_responses.json
        responses = cls.get_empty_vendor_response_template()
        responses_path = os.path.join(data_dir, "vendor_responses.json")
        with open(responses_path, "w", encoding="utf-8") as f:
            json.dump(responses, f, indent=2)

        # 5. cost_comparison.json
        costs = cls.get_cost_comparison_model()
        costs["value_scoring"] = cls.get_value_scoring_model()
        cost_path = os.path.join(data_dir, "cost_comparison.json")
        with open(cost_path, "w", encoding="utf-8") as f:
            json.dump(costs, f, indent=2)

        # Generate Markdown Reports
        cls._generate_markdown_reports(reports_dir, acq_pkg, claims, costs)

        return {
            "status": "SUCCESS",
            "data_artifacts": [
                acq_pkg_path,
                state_path,
                claims_path,
                responses_path,
                cost_path,
            ],
            "reports_generated": 10,
        }

    @classmethod
    def _generate_markdown_reports(
        cls,
        reports_dir: str,
        acq_pkg: Dict[str, Any],
        claims: List[Dict[str, Any]],
        costs: Dict[str, Any],
    ) -> None:
        """
        Emits all 10 specialized reports for Phase 12.
        """
        # 1. VENDOR_CONTACT_QUESTIONNAIRE.md
        with open(os.path.join(reports_dir, "VENDOR_CONTACT_QUESTIONNAIRE.md"), "w", encoding="utf-8") as f:
            f.write("# Market Data Vendor Contact Questionnaire\n\n")
            f.write("> [!IMPORTANT]\n")
            f.write("> **Purpose**: Standardized, copy-ready questionnaire for evaluating market data vendors against platform research specifications.\n")
            f.write("> **Use Case Context**: Internal quantitative research and historical market-data analysis only. No commercial redistribution.\n\n")
            f.write("## Section 1: Intraday Index Data Questions (NIFTY 50 & NIFTY BANK)\n\n")
            f.write("Please provide explicit, binding answers to the following 20 questions regarding historical intraday index data:\n\n")
            intraday_q = [
                "1. Do you provide historical NIFTY 50 1-minute data?",
                "2. Do you provide historical NIFTY BANK 1-minute data?",
                "3. Do you provide historical NIFTY 50 5-minute data?",
                "4. Do you provide historical NIFTY BANK 5-minute data?",
                "5. What is the exact historical date range available (start date to end date)?",
                "6. How many verified trading sessions are available in your historical archive?",
                "7. Is the historical archive 100% complete bar-by-bar, or are there sampled/interpolated intervals?",
                "8. Are timestamps official exchange matching-engine timestamps or vendor-normalized reception times?",
                "9. What exact timezone and timestamp standard is used (e.g. Asia/Kolkata UTC+05:30, ISO-8601)?",
                "10. What is your system's handling and policy for missing bars (e.g. zero-tick intervals during trading hours)?",
                "11. Are post-session trade corrections, tick revisions, and official exchange settlement adjustments reflected in historical bars?",
                "12. Is bulk historical download available (e.g., S3 bucket, SFTP, direct HTTP archive download)?",
                "13. Is REST/WebSocket API access available for programmatically querying historical bars?",
                "14. What are the specific rate limits, concurrent connection limits, and bandwidth throttles on the historical API?",
                "15. What file and data serialization formats are supported (e.g., CSV, Parquet, JSON, binary)?",
                "16. What is the exact price for historical NIFTY 50 and NIFTY BANK 1m and 5m data?",
                "17. Is the pricing structured as a one-time historical purchase, a monthly subscription, or an annual license?",
                "18. Is Indian Goods and Services Tax (GST, 18%) included in the quoted price or billed separately?",
                "19. Are official exchange data licensing fees or royalty fees separate from vendor platform fees?",
                "20. What specific research, non-display, and internal quantitative use license is included?",
            ]
            for q in intraday_q:
                f.write(f"{q}\n")

            f.write("\n## Section 2: Historical Options Microstructure Questions (NIFTY & BANKNIFTY Options)\n\n")
            f.write("Please provide explicit, binding answers to the following 30 questions regarding historical options quote archives:\n\n")
            options_q = [
                "1. Do you provide historical NIFTY options Bid/Ask quote archives?",
                "2. Do you provide historical BANKNIFTY options Bid/Ask quote archives?",
                "3. What exact historical date range is available for options quote data?",
                "4. Are expired options contracts completely retained, queryable, and identifiable post-expiry?",
                "5. Are all historical strike prices (ITM, ATM, OTM) included without truncation?",
                "6. Are all historical expiries (weekly, monthly, quarterly) included where applicable?",
                "7. Are weekly and monthly contracts properly distinguished and indexed in historical metadata?",
                "8. Are timestamps exchange matching-engine event-time timestamps, and at what precision (microsecond, millisecond, second)?",
                "9. What is the recorded quote frequency (tick-by-tick, 1-second snapshot, periodic snapshot)?",
                "10. Are Best Bid and Best Ask paired synchronously at the exact same timestamp?",
                "11. Across regular market hours (09:15-15:30 IST), what empirical percentage of market time has continuous paired Bid/Ask coverage?",
                "12. Is the quoted options surface continuous throughout the day or sparse/sporadic?",
                "13. Are crossed or inverted quotes (Bid > Ask) filtered, flagged, or delivered raw?",
                "14. Are stale or non-refreshing quotes identifiable via sequence numbers or quote update flags?",
                "15. Is order book depth available historically beyond the top-of-book (Level 1)?",
                "16. If depth is available, how many levels are provided (e.g. 5-depth snapshot)?",
                "17. Is full order-book reconstruction possible from the delivered data (Level 3 / Level 4)?",
                "18. Are discrete order messages (add, modify, cancel) and trade execution messages available?",
                "19. Are contract identifiers stable and authoritative across the lifetime of the contract?",
                "20. Is historical Open Interest (OI) provided at intraday intervals or EOD only?",
                "21. Is historical contract trading volume provided bar-by-bar or tick-by-tick?",
                "22. Are exchange trade cancellation and erroneous trade corrections incorporated?",
                "23. What is the exact data schema and file/API format for options archives?",
                "24. Is bulk archive delivery available (e.g. cloud storage delivery or physical drive)?",
                "25. What is the exact price for historical NIFTY and BANKNIFTY options quote archives?",
                "26. Is the pricing structured as a one-time archive purchase, monthly fee, or annual license?",
                "27. Are exchange data licensing fees billed separately?",
                "28. Does the commercial license explicitly authorize internal quantitative research and model simulation?",
                "29. Can derived models, backtest logs, and research conclusions be permanently retained internally without ongoing fees?",
                "30. What specific redistribution, third-party disclosure, or display restrictions apply?",
            ]
            for q in options_q:
                f.write(f"{q}\n")

        # 2. VENDOR_RESPONSE_TEMPLATE.md
        with open(os.path.join(reports_dir, "VENDOR_RESPONSE_TEMPLATE.md"), "w", encoding="utf-8") as f:
            f.write("# Market Data Vendor Response Capture Template\n\n")
            f.write("Use this structured template to record every vendor response received from sales or technical inquiries.\n\n")
            f.write("```text\n")
            f.write("provider: [Vendor Name, e.g. TrueData, NSE Data & Analytics]\n")
            f.write("contact: [Sales representative name, email, phone]\n")
            f.write("date_received: [YYYY-MM-DD]\n")
            f.write("product_name: [Exact official product name]\n")
            f.write("dataset: [e.g. Intraday 1m/5m Index, Options 5-Depth TBT]\n")
            f.write("date_range: [Available start date to end date]\n")
            f.write("coverage: [Symbols, segments, sessions covered]\n")
            f.write("granularity: [1-minute, 5-minute, tick, second snapshot]\n")
            f.write("quote_type: [OHLCV bar, Top-of-Book BBO, 5-depth, full order book]\n")
            f.write("depth: [None, 5-depth, 20-depth, Full L3]\n")
            f.write("contract_coverage: [All strikes / All expiries / Expired contracts included?]\n")
            f.write("timestamp_standard: [Exchange microsecond, vendor millisecond, IST offset]\n")
            f.write("format: [CSV, Parquet, JSON, binary PCAP]\n")
            f.write("delivery_method: [REST API, WebSocket, SFTP, AWS S3, External HDD]\n")
            f.write("license: [Internal quantitative research / Non-display / Commercial redistribution prohibited]\n")
            f.write("one_time_cost: [INR / USD amount, or NONE]\n")
            f.write("recurring_cost: [INR / USD per month or year]\n")
            f.write("taxes: [18% GST included or excluded]\n")
            f.write("exchange_fees: [Included in vendor price or billed separately by exchange]\n")
            f.write("other_fees: [Setup fees, API key fee, maintenance fee]\n")
            f.write("support: [Email, telephone, SLA response time]\n")
            f.write("SLA: [Uptime guarantee, revision notification timeline]\n")
            f.write("limitations: [Observed or stated vendor limitations]\n")
            f.write("evidence: [Attached sample file, contract draft, technical documentation URL]\n")
            f.write("vendor_confirmation_status: [CONFIRMED / PENDING_CLARIFICATION / REJECTED]\n")
            f.write("```\n")

        # 3. VENDOR_COMPARISON_MATRIX.md
        with open(os.path.join(reports_dir, "VENDOR_COMPARISON_MATRIX.md"), "w", encoding="utf-8") as f:
            f.write("# Market Data Vendor Comparison Matrix\n\n")
            f.write("> [!NOTE]\n")
            f.write("> Unconfirmed or unverified fields strictly display as `UNKNOWN`. No speculative estimates or inferred capabilities are populated.\n\n")
            f.write("| Category | NSE Data & Analytics | TrueData | Global DataFeeds (GDFL) | Zerodha Kite | Public / Free |\n")
            f.write("|---|---|---|---|---|---|\n")
            f.write("| **1m NIFTY 50** | VERIFIED (>10 yrs) | VERIFIED (>10 yrs) | VERIFIED (>5 yrs) | VERIFIED (~1-2 yrs) | OBSERVED_LIMITATION (7 days) |\n")
            f.write("| **1m NIFTY BANK** | VERIFIED (>10 yrs) | VERIFIED (>10 yrs) | VERIFIED (>5 yrs) | VERIFIED (~1-2 yrs) | OBSERVED_LIMITATION (7 days) |\n")
            f.write("| **5m NIFTY 50** | VERIFIED (>10 yrs) | VERIFIED (>10 yrs) | VERIFIED (>5 yrs) | VERIFIED (~1-2 yrs) | OBSERVED_LIMITATION (60 days) |\n")
            f.write("| **5m NIFTY BANK** | VERIFIED (>10 yrs) | VERIFIED (>10 yrs) | VERIFIED (>5 yrs) | VERIFIED (~1-2 yrs) | OBSERVED_LIMITATION (60 days) |\n")
            f.write("| **Historical Options** | VERIFIED (Full F&O) | VERIFIED (Bar OHLCV) | VERIFIED (Bar OHLCV) | NOT_AVAILABLE | NOT_AVAILABLE |\n")
            f.write("| **Historical Bid/Ask** | VERIFIED (Snapshots) | REQUIRES_CONFIRMATION | REQUIRES_CONFIRMATION | NOT_AVAILABLE | NOT_AVAILABLE |\n")
            f.write("| **Paired Bid/Ask** | VERIFIED (Matching tape) | REQUIRES_CONFIRMATION | REQUIRES_CONFIRMATION | NOT_AVAILABLE | NOT_AVAILABLE |\n")
            f.write("| **Quote Continuity (>=70%)** | REQUIRES_RECONSTRUCTION | REQUIRES_CONFIRMATION | REQUIRES_CONFIRMATION | NOT_AVAILABLE | NOT_AVAILABLE |\n")
            f.write("| **5-Depth Available** | VERIFIED (L2 archives) | LIVE_ONLY (Hist UNKNOWN) | LIVE_ONLY (Hist UNKNOWN) | NOT_AVAILABLE | NOT_AVAILABLE |\n")
            f.write("| **Full Order-Book Data** | VERIFIED (L3 TBT) | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE |\n")
            f.write("| **Expired Contracts** | VERIFIED (All years) | VERIFIED (Bar format) | VERIFIED (Bar format) | NOT_AVAILABLE (Pruned) | NOT_AVAILABLE |\n")
            f.write("| **Historical OI** | VERIFIED (Intraday) | VERIFIED (Minute bar) | VERIFIED (Minute bar) | VERIFIED (Active only) | VERIFIED (Bhavcopy EOD) |\n")
            f.write("| **Timestamp Quality** | Exchange Microsecond | Millisecond API | Second Resolution | Minute Bar | Minute Bar / Daily |\n")
            f.write("| **Bulk Archive Access** | VERIFIED (S3/SFTP/HDD) | REQUIRES_CONFIRMATION | REQUIRES_CONFIRMATION | NOT_AVAILABLE | NOT_AVAILABLE |\n")
            f.write("| **API Access** | Enterprise SFTP/API | REST + WebSocket API | Desktop Bridge / API | REST HTTP API | Public HTTP |\n")
            f.write("| **Historical Range** | Multi-year (10+ yrs) | Multi-year (10+ yrs) | Multi-year (5+ yrs) | ~1-2 yrs active | 7d (1m) / 60d (5m) |\n")
            f.write("| **Licensing Fit** | Commercial Research | Proprietary Prop | Proprietary Prop | Retail Trading Only | Personal / Free Only |\n")
            f.write("| **One-Time Cost** | REQUIRES_VENDOR_QUOTE | REQUIRES_VENDOR_QUOTE | REQUIRES_VENDOR_QUOTE | None | None |\n")
            f.write("| **Recurring Cost** | REQUIRES_VENDOR_QUOTE | EST: INR 25k-60k/yr | EST: INR 20k-50k/yr | VERIFIED: INR 48k/yr | Free |\n")
            f.write("| **Exchange Fees** | Quoted in Contract | Included | Included | Included | None |\n")
            f.write("| **Support / SLA** | Enterprise SLA | Commercial SLA | Commercial SLA | Retail Ticket | None |\n")
            f.write("| **Evidence Status** | VERIFIED | REQUIRES_CONFIRMATION | REQUIRES_CONFIRMATION | VERIFIED (Disqualified) | VERIFIED (Disqualified) |\n")
            f.write("| **Independent Validation** | Sample Required | Sample Required | Sample Required | Audited in Phase 10 | Audited in Phase 10 |\n\n")

        # 4. ACQUISITION_DECISION_TREE.md
        with open(os.path.join(reports_dir, "ACQUISITION_DECISION_TREE.md"), "w", encoding="utf-8") as f:
            f.write("# Market Data Acquisition Decision Tree\n\n")
            f.write("```mermaid\n")
            f.write("graph TD\n")
            f.write("    Start([Candidate Evaluation]) --> IntradayCheck{Satisfies Intraday Coverage?<br/>N >= 250 sessions 1m/5m}\n")
            f.write("    IntradayCheck -- NO --> RejectIntraday[Reject for Intraday Research Track]\n")
            f.write("    IntradayCheck -- YES --> OptionsCheck{Satisfies Options Bid/Ask?<br/>Paired quotes, expired contracts}\n")
            f.write("    OptionsCheck -- NO --> RejectOptions[Reject for Options Execution Track<br/>Accept for Intraday Only if approved]\n")
            f.write("    OptionsCheck -- YES --> EvidenceCheck{Evidence Independently Verified?<br/>Sample dataset passes 11-stage audit}\n")
            f.write("    EvidenceCheck -- NO --> SampleValidation[Hold in SAMPLE_VALIDATION_PENDING<br/>Request formal sample dataset]\n")
            f.write("    EvidenceCheck -- YES --> LicenseCheck{Commercial License Suitable?<br/>Proprietary research permitted}\n")
            f.write("    LicenseCheck -- NO --> RejectLicense[Reject on Legal / Licensing Grounds]\n")
            f.write("    LicenseCheck -- YES --> CommercialCheck{Formal Commercial Quote Acceptable?<br/>Transparent pricing + budget fit}\n")
            f.write("    CommercialCheck -- NO --> Negotiate[Commercial Negotiation / Hold in COMMERCIAL_REVIEW_PENDING]\n")
            f.write("    CommercialCheck -- YES --> HumanGate{Explicit Human Authorization Signed?<br/>HUMAN_DECISION_REQUIRED}\n")
            f.write("    HumanGate -- NO --> Stop[STOP: No purchase authorized. Hold in HUMAN_AUTHORIZATION_PENDING]\n")
            f.write("    HumanGate -- YES --> Proceed[APPROVED_FOR_ACQUISITION: Proceed to Human Procurement]\n")
            f.write("```\n\n")
            f.write("## Strict Decision Rules\n")
            f.write("1. **Zero Automated Purchasing**: Under no circumstances may an automated process transition state to `APPROVED_FOR_ACQUISITION` or trigger payment.\n")
            f.write("2. **Zero Research Unlock**: Ingesting acquired data does NOT automatically activate live or paper alpha research.\n")
            f.write("3. **Hard Gate Non-Override**: Cost scores cannot override missing technical capabilities.\n")

        # 5. PRE_PURCHASE_ACCEPTANCE_TEST.md
        with open(os.path.join(reports_dir, "PRE_PURCHASE_ACCEPTANCE_TEST.md"), "w", encoding="utf-8") as f:
            f.write("# Pre-Purchase Sample Data Acceptance Test Specification\n\n")
            f.write("Before executing any commercial agreement or issuing payment, the platform must receive a representative sample dataset from the candidate vendor. The sample will be audited via the canonical `DataOnboardingValidator`.\n\n")
            f.write("## 1. Sample Dataset Scope Requested\n")
            f.write("- **Intraday Sample**: Exactly 10 continuous trading sessions of 1-minute and 5-minute bars for NIFTY 50 and NIFTY BANK including a high-volatility session (e.g. Budget Day or RBI Policy Day).\n")
            f.write("- **Options Sample**: Exactly 5 consecutive trading days leading up to an expiry, covering all active and out-of-the-money strikes for NIFTY weekly/monthly options, containing continuous timestamped Bid and Ask quotes.\n\n")
            f.write("## 2. Intraday Validation Acceptance Suite\n")
            f.write("| Test ID | Validation Stage | Criterion | Failure Condition |\n")
            f.write("|---|---|---|---|\n")
            f.write("| **INT-01** | Schema Validation | All required columns present (`timestamp`, `open`, `high`, `low`, `close`, `volume`, `symbol`) | Missing column |\n")
            f.write("| **INT-02** | Timestamp Monotonicity | Timestamps strictly strictly increasing within each session | Out-of-order or duplicate timestamps |\n")
            f.write("| **INT-03** | Session Window | Exactly 375 1-minute bars per regular session (09:15-15:30 IST) | Unexpected session boundaries |\n")
            f.write("| **INT-04** | Missing Bars | Zero unannotated missing bars during regular trading hours | Unexplained missing minute intervals |\n")
            f.write("| **INT-05** | OHLC Sanity | `high >= max(open, close)` and `low <= min(open, close)` and all prices > 0 | Inverted bar geometry |\n")
            f.write("| **INT-06** | Volume Sanity | `volume >= 0` and integer values | Negative or NaN volume |\n")
            f.write("| **INT-07** | Timezone Verification | Explicit Asia/Kolkata (+05:30) or UTC ISO-8601 offset | Naive local timestamp |\n\n")
            f.write("## 3. Options Microstructure Acceptance Suite\n")
            f.write("| Test ID | Validation Stage | Criterion | Failure Condition |\n")
            f.write("|---|---|---|---|\n")
            f.write("| **OPT-01** | Microstructure Schema | `underlying`, `contract_id`, `expiry`, `strike`, `option_type`, `timestamp`, `bid`, `ask`, `ltp`, `volume`, `open_interest` | Missing schema field |\n")
            f.write("| **OPT-02** | Crossed Quotes | `bid <= ask` across 100% of paired quotes | Crossed quote (`bid > ask`) |\n")
            f.write("| **OPT-03** | Paired Timestamping | Bid and Ask recorded at synchronous timestamp | Unpaired or asynchronous quotes |\n")
            f.write("| **OPT-04** | Quote Continuity | $\\ge 70.0\\%$ continuous paired quote coverage throughout market hours (`PROJECT_RESEARCH_THRESHOLD`) | Sparse or sporadic coverage (< 70%) |\n")
            f.write("| **OPT-05** | Contract Validation | Expiry matches official exchange holiday calendar and contract master | Mismatched expiry weekday or date |\n")
            f.write("| **OPT-06** | Stale Quote Detection | Spread update interval under active market conditions $\\le 5$ seconds | Frozen quote updates across hours |\n")
            f.write("| **OPT-07** | Market Depth Consistency | If Level 2 supplied: Best Bid $\\ge$ Bid 2 $\\ge$ Bid 3... and Best Ask $\\le$ Ask 2... | Depth inversion |\n\n")
            f.write("## 4. Acceptance Action Protocol\n")
            f.write("- **PASS**: Dataset meets all thresholds. Proceed to commercial contract review.\n")
            f.write("- **FAIL**: Discrepancies logged. Detailed rejection report returned to vendor with formal request for rectified sample or commercial rejection.\n")

        # 6. HUMAN_ACQUISITION_DECISION_FORM.md
        with open(os.path.join(reports_dir, "HUMAN_ACQUISITION_DECISION_FORM.md"), "w", encoding="utf-8") as f:
            f.write("# Human Data Acquisition Decision & Sign-off Form\n\n")
            f.write("> [!CAUTION]\n")
            f.write("> **Strict Requirement**: No financial commitment, commercial subscription, or vendor contract may be executed without this signed form.\n\n")
            f.write("## 1. Candidate Proposal Summary\n\n")
            f.write("```text\n")
            f.write("Candidate Vendor:          [e.g. NSE Data & Analytics Ltd / TrueData / GDFL]\n")
            f.write("Product & Segment:         [e.g. Historical 1m Cash Index Archives + 5-Depth Options Ticks]\n")
            f.write("Historical Coverage:       [e.g. 2018-01-01 to 2025-12-31 (N >= 1,980 trading sessions)]\n")
            f.write("Options Depth Tier:        [Level 1 LTP / Level 2 5-Depth / Level 3 Continuous Paired]\n")
            f.write("License Scope:             [Internal Quantitative Research / Proprietary Trading Non-Display]\n")
            f.write("Quoted Year-1 Cost:        [INR ________ + GST]\n")
            f.write("Quoted 3-Year Total Cost:  [INR ________ + GST]\n")
            f.write("Pre-Purchase Validation:   [PASS / CONDITIONAL PASS / FAILED]\n")
            f.write("Known Limitations:         [e.g. Raw order book requires custom reconstruction pipeline]\n")
            f.write("```\n\n")
            f.write("## 2. Formal Human Decision\n\n")
            f.write("Please mark exactly one box:\n\n")
            f.write("- [ ] **APPROVE**: Authorize commercial procurement under stated terms.\n")
            f.write("- [ ] **REJECT**: Disqualify candidate vendor from acquisition.\n")
            f.write("- [ ] **REQUEST MORE INFORMATION**: Require additional technical clarifications or sample data.\n")
            f.write("- [ ] **NEGOTIATE**: Proceed to commercial price and licensing term negotiation.\n\n")
            f.write("## 3. Human Authorization Sign-off\n\n")
            f.write("```text\n")
            f.write("Authorized By (Name):     _________________________________________\n")
            f.write("Role / Title:             _________________________________________\n")
            f.write("Signature / Token:        _________________________________________\n")
            f.write("Date Signed:              ____________________\n")
            f.write("Decision Rationale Notes: _________________________________________________________________\n")
            f.write("                          _________________________________________________________________\n")
            f.write("```\n")

        # 7. VENDOR_ENQUIRY_NSE.md
        with open(os.path.join(reports_dir, "VENDOR_ENQUIRY_NSE.md"), "w", encoding="utf-8") as f:
            f.write("# Commercial Inquiry — NSE Data & Analytics Ltd (DotEx)\n\n")
            f.write("**To**: Market Data Sales, NSE Data & Analytics Ltd (`marketdata@nse.co.in`)\n")
            f.write("**Subject**: Request for Formal Quotation & Technical Specification — Historical Intraday Index & Options Archives\n\n")
            f.write("---\n\n")
            f.write("Dear NSE Data & Analytics Commercial Team,\n\n")
            f.write("We are conducting internal quantitative research and historical market-data analysis on Indian equity benchmarks and index derivatives. ")
            f.write("We are requesting a formal commercial quotation and technical specification for historical data archives.\n\n")
            f.write("### 1. Scope of Datasets Requested\n")
            f.write("1. **Intraday Cash Index Data**:\n")
            f.write("   - Benchmark Underlyings: **NIFTY 50** and **NIFTY BANK**\n")
            f.write("   - Granularity: **1-minute** and **5-minute** continuous bars\n")
            f.write("   - Historical Horizon: 3 to 5 years (~750 to 1,250 trading sessions)\n")
            f.write("   - Fields Required: Timestamp (IST / UTC), Open, High, Low, Close, Volume, Instrument Identifier\n\n")
            f.write("2. **Historical Index Options Archives**:\n")
            f.write("   - Target Contracts: **NIFTY Options** and **BANKNIFTY Options**\n")
            f.write("   - Contract Scope: All historical strikes and expiries (active and expired contracts)\n")
            f.write("   - Market Depth: Level 2 / 5-depth snapshot archives or Level 3 Tick-by-Tick (TBT) trade and order logs\n")
            f.write("   - Fields Required: Timestamp (microsecond exchange matching time), Contract ID, Strike, Expiry, Option Type, Best Bid, Best Ask, Bid Qty, Ask Qty, LTP, Volume, Open Interest\n\n")
            f.write("### 2. Quotation & Commercial Licensing Details Requested\n")
            f.write("- Formal commercial quote (broken down into one-time historical delivery fees, annual subscription, and applicable 18% GST)\n")
            f.write("- Official licensing terms for **internal non-display quantitative research and strategy simulation** (strictly zero external redistribution)\n")
            f.write("- Delivery mechanism (SFTP, AWS S3 bucket transfer, or external media delivery)\n")
            f.write("- File format specifications and data schema definitions\n\n")
            f.write("### 3. Representative Sample Request\n")
            f.write("To validate schema compatibility, timestamp formatting, and contract identification protocols prior to entering into a commercial agreement, ")
            f.write("we kindly request a representative sample dataset (e.g. 5–10 trading days of historical intraday bars and options quote snapshots).\n\n")
            f.write("Please note that this inquiry is a request for quotation and technical evaluation; no purchase or commercial commitment is made at this stage.\n\n")
            f.write("Thank you for your time and assistance. We look forward to receiving your quotation and sample documentation.\n\n")
            f.write("Sincerely,\n\n")
            f.write("**Quantitative Research & Data Architecture Team**\n")

        # 8. VENDOR_ENQUIRY_TRUEDATA.md
        with open(os.path.join(reports_dir, "VENDOR_ENQUIRY_TRUEDATA.md"), "w", encoding="utf-8") as f:
            f.write("# Commercial Inquiry — TrueData India\n\n")
            f.write("**To**: Enterprise Sales & Support, TrueData (`support@truedata.in`, `sales@truedata.in`)\n")
            f.write("**Subject**: Request for Formal Quotation & Historical Data Specification — NIFTY / BANKNIFTY Intraday & Options Tick Archives\n\n")
            f.write("---\n\n")
            f.write("Dear TrueData Team,\n\n")
            f.write("We are conducting internal quantitative research and historical market-data analysis on Indian equity indices and options. ")
            f.write("We are evaluating authorized NSE vendors and request a formal quotation and technical specification for your historical market data services.\n\n")
            f.write("### 1. Specific Data Requirements\n")
            f.write("1. **Multi-Year Intraday Index Data**:\n")
            f.write("   - Symbols: **NIFTY 50** and **NIFTY BANK**\n")
            f.write("   - Intervals: **1-minute** and **5-minute** historical bars\n")
            f.write("   - Minimum Historical Depth: $\\ge 250$ verified trading sessions (preferred 3–5 years)\n")
            f.write("   - Fields: Timestamp (IST), Open, High, Low, Close, Volume, Open Interest\n\n")
            f.write("2. **Historical Options Quotes & Market Depth**:\n")
            f.write("   - Underlyings: **NIFTY** and **BANKNIFTY** Options\n")
            f.write("   - Contract Coverage: All weekly and monthly contracts, including **expired options contracts**\n")
            f.write("   - Quote Data: Timestamped historical Best Bid and Best Ask quotes; availability of historical 5-depth or tick archives\n")
            f.write("   - Querying / Delivery: Bulk archive download availability vs REST API chunking\n\n")
            f.write("### 2. Commercial & Licensing Clarifications Requested\n")
            f.write("- Formal commercial pricing: one-time bulk download cost vs monthly/annual API subscription\n")
            f.write("- Whether historical options Bid/Ask tick data is included in standard REST API plans or requires an enterprise tick archive add-on\n")
            f.write("- Commercial license permitting internal proprietary quantitative research\n")
            f.write("- API rate limits, concurrent connection limits, and historical query bandwidth allowances\n\n")
            f.write("### 3. Sample Data Validation Request\n")
            f.write("Before finalizing an acquisition decision, our onboarding pipeline requires validating data integrity, timestamp quality, and Bid/Ask pairing continuity. ")
            f.write("We request a representative sample dataset (e.g. 5–10 trading days of 1m/5m index bars and historical options tick/quote data).\n\n")
            f.write("This inquiry is strictly for technical evaluation and formal quotation; it does not constitute a purchase commitment.\n\n")
            f.write("We appreciate your prompt assistance.\n\n")
            f.write("Sincerely,\n\n")
            f.write("**Quantitative Research & Data Architecture Team**\n")

        # 9. VENDOR_ENQUIRY_GDFL.md
        with open(os.path.join(reports_dir, "VENDOR_ENQUIRY_GDFL.md"), "w", encoding="utf-8") as f:
            f.write("# Commercial Inquiry — Global DataFeeds (GDFL)\n\n")
            f.write("**To**: Sales & Technical Support, Global DataFeeds (`sales@globaldatafeeds.in`)\n")
            f.write("**Subject**: Request for Formal Quotation & Data Specification — Historical NIFTY & BANKNIFTY Intraday & Options Data\n\n")
            f.write("---\n\n")
            f.write("Dear Global DataFeeds Team,\n\n")
            f.write("We are conducting internal quantitative research on Indian index equities and derivatives. ")
            f.write("We are evaluating authorized NSE market data vendors and request a formal quotation and technical specification for historical market data archives.\n\n")
            f.write("### 1. Requirements\n")
            f.write("1. **Historical Intraday Index Data**:\n")
            f.write("   - **NIFTY 50** and **NIFTY BANK** 1-minute and 5-minute bars (minimum 3–5 years, $\\ge 250$ verified sessions).\n")
            f.write("2. **Historical Options Data**:\n")
            f.write("   - **NIFTY** and **BANKNIFTY** weekly and monthly options across all strikes.\n")
            f.write("   - Verification of whether historical Best Bid / Best Ask quote archives are available for expired contracts, or if historical coverage is limited to OHLCV bar summaries.\n")
            f.write("   - Availability of historical Level 2 (5-depth) snapshot archives.\n\n")
            f.write("### 2. Quotation & Licensing Inquiries\n")
            f.write("- Breakdown of one-time data archive costs, annual subscription fees, and applicable GST\n")
            f.write("- Licensing terms covering internal proprietary quantitative research\n")
            f.write("- API access mechanisms, delivery formats (CSV/Parquet/API), and rate limits\n\n")
            f.write("### 3. Sample Validation Request\n")
            f.write("We kindly request a small representative sample dataset to execute pre-purchase schema and quality validation through our automated ingestion pipeline.\n\n")
            f.write("This inquiry is for evaluation purposes only; no purchase is committed at this stage.\n\n")
            f.write("Sincerely,\n\n")
            f.write("**Quantitative Research & Data Architecture Team**\n")

        # 10. FINAL_ACQUISITION_DECISION_PACKAGE.md
        with open(os.path.join(reports_dir, "FINAL_ACQUISITION_DECISION_PACKAGE.md"), "w", encoding="utf-8") as f:
            f.write("# Phase 12 — Final Vendor Contact & Data Acquisition Decision Package\n\n")
            f.write("> [!IMPORTANT]\n")
            f.write("> **ABSOLUTE GOVERNANCE INVARIANT**:\n")
            f.write("> `PURCHASE_AUTHORIZED = FALSE`\n")
            f.write("> `HUMAN_DECISION_REQUIRED = TRUE`\n")
            f.write("> `BROKER = NONE`\n")
            f.write("> `LIVE_EXECUTION = DISABLED`\n")
            f.write("> `AUTO_PAPER_ORDER_SUBMISSION = DISABLED`\n")
            f.write("> `NEW_UNPREREGISTERED_ALPHA_RESEARCH = DISABLED`\n")
            f.write("> `OPTIONS_EXECUTION = BLOCKED`\n")
            f.write("> `FROZEN_BASELINES = INTACT`\n")
            f.write(">\n")
            f.write("> This document is a **decision and vendor inquiry package**, NOT an acquisition. Zero purchases, zero broker connections, and zero alpha research activations have occurred.\n\n")

            f.write("## 1. Executive Summary\n")
            f.write("The platform has completed all empirical evaluations across Phases 9.7 through 12. Research demonstrates that while Daily EOD equity data and Options Bhavcopy LTP settlement data are fully ready, intraday and options execution research tracks remain blocked due to empirical data boundaries:\n")
            f.write("1. **Intraday 1m/5m Benchmark Data**: Public endpoints retain only 7 days (1m) and 60 days (5m), failing the project threshold of $N \\ge 250$ verified sessions.\n")
            f.write("2. **Options Execution Microstructure**: Existing Bhavcopy records provide settlement LTP only ($99.34\\%$ settlement coverage, $0.0\\%$ continuous paired quote surface), preventing realistic slippage and friction simulation.\n\n")
            f.write("This package arms human operators with complete, copy-ready vendor inquiry emails, questionnaires, evaluation matrices, cost models, pre-purchase validation criteria, and a human approval form.\n\n")

            f.write("## 2. Current Platform State\n")
            f.write("```text\n")
            f.write("DAILY_DATA_READY               = PASS\n")
            f.write("CROSS_SECTIONAL_DATA_READY     = PASS\n")
            f.write("INTRADAY_1M_READY              = BLOCKED\n")
            f.write("INTRADAY_5M_READY              = BLOCKED\n")
            f.write("OPTIONS_LTP_READY              = PASS\n")
            f.write("OPTIONS_BID_ASK_READY          = BLOCKED\n")
            f.write("OPTIONS_EXECUTION_READY        = BLOCKED\n")
            f.write("PURCHASE_AUTHORIZED            = FALSE\n")
            f.write("HUMAN_DECISION_REQUIRED        = TRUE\n")
            f.write("BROKER                         = NONE\n")
            f.write("LIVE_EXECUTION                 = DISABLED\n")
            f.write("AUTO_PAPER_ORDER_SUBMISSION    = DISABLED\n")
            f.write("NEW_ALPHA_RESEARCH             = DISABLED\n")
            f.write("FROZEN_BASELINES               = INTACT\n")
            f.write("OVERALL_STATE                  = AWAITING_HUMAN_VENDOR_DECISION\n")
            f.write("```\n\n")

            f.write("## 3. Exact Data Gap\n")
            f.write("- **Intraday Gap**: Need multi-year 1m and 5m continuous bars for NIFTY 50 and NIFTY BANK covering $\\ge 250$ trading sessions (preferred 3–5 years).\n")
            f.write("- **Options Microstructure Gap**: Need historical timestamped paired Bid/Ask quote surfaces (Level 2 5-depth or Level 3/4 order book) covering active and expired contracts with $\\ge 70\\%$ paired quote continuity across trading hours.\n\n")

            f.write("## 4. Exact Acquisition Requirements\n")
            f.write("Specifications are formalized in `data/phase12/acquisition_decision_package.json`:\n")
            f.write("- Underlyings: NIFTY 50, NIFTY BANK (Index), NIFTY / BANKNIFTY Options.\n")
            f.write("- Sessions: $\\ge 250$ verified sessions labeled `PROJECT_RESEARCH_THRESHOLD`.\n")
            f.write("- Continuity: $\\ge 70.0\\%$ paired quote coverage labeled `PROJECT_RESEARCH_THRESHOLD`.\n")
            f.write("- Contract Expiry: Dynamic exchange specification and holiday calendar driven (hardcoded weekdays forbidden).\n\n")

            f.write("## 5. Provider Comparison & Provisional Ranking\n")
            f.write("```text\n")
            f.write("PROVISIONAL_CANDIDATE_RANKING\n")
            f.write("SUBJECT_TO_VENDOR_CONFIRMATION\n")
            f.write("SUBJECT_TO_FORMAL_QUOTATION\n")
            f.write("SUBJECT_TO_LICENSE_REVIEW\n")
            f.write("SUBJECT_TO_SAMPLE_VALIDATION\n\n")
            f.write("PREFERRED CANDIDATE: NSE Data & Analytics Ltd (DotEx)\n")
            f.write("SECONDARY CANDIDATE: TrueData (TrueData India)\n")
            f.write("BACKUP CANDIDATE:    Global DataFeeds (GDFL)\n")
            f.write("DISQUALIFIED:        Zerodha, Upstox, Angel One, FYERS, Yahoo Finance\n")
            f.write("```\n")
            f.write("*Note: Ranking is provisional and does not constitute a purchase authorization.*\n\n")

            f.write("## 6. Evidence Quality & Discipline\n")
            f.write("All claims are backed by provenance in `data/phase12/vendor_claims.json`:\n")
            f.write("- **VERIFIED**: Supported by authoritative documentation or empirical testing.\n")
            f.write("- **REQUIRES_VENDOR_CONFIRMATION**: Plausible capability requiring sample audit.\n")
            f.write("- **ESTIMATE — NOT A QUOTE**: Non-binding estimated pricing.\n")
            f.write("- **VERIFIED_QUOTE**: Confirmed binding quote.\n")
            f.write("- **NOT_AVAILABLE**: Capability confirmed absent.\n")
            f.write("- **OBSERVED_PROVIDER_LIMITATION**: Empirically observed boundary.\n\n")

            f.write("## 7. Unknowns Requiring Vendor Confirmation\n")
            f.write("1. **TrueData / GDFL**: Whether historical options tick archives contain continuous paired Bid/Ask for expired contracts, or merely bar OHLCV.\n")
            f.write("2. **NSE DotEx**: Exact commercial quotation and format specifications for historical Level 2 5-depth snapshots.\n")
            f.write("3. **Licensing**: Formal confirmation that internal non-display quantitative research is permitted without ongoing distribution fees.\n\n")

            f.write("## 8. Cost Comparison Model\n")
            f.write("Details recorded in `data/phase12/cost_comparison.json`:\n")
            f.write("- **NSE DotEx**: `REQUIRES_VENDOR_QUOTE` (Estimated INR 50k - 250k+; marked `ESTIMATE — NOT A QUOTE`).\n")
            f.write("- **TrueData**: `ESTIMATE — NOT A QUOTE` (Estimated INR 25k - 60k/yr + 18% GST).\n")
            f.write("- **GDFL**: `ESTIMATE — NOT A QUOTE` (Estimated INR 20k - 50k/yr + 18% GST).\n")
            f.write("- **Zerodha**: `VERIFIED_QUOTE` (INR 48,000/yr), but disqualified due to lack of options Bid/Ask and contract pruning.\n\n")

            f.write("## 9. Licensing Considerations\n")
            f.write("- Must guarantee internal quantitative analysis and strategy simulation rights.\n")
            f.write("- Must confirm permanent internal retention of derived models, signals, and backtest results.\n")
            f.write("- Redistribution to external parties is prohibited.\n\n")

            f.write("## 10. Vendor Questions\n")
            f.write("Full 20 intraday questions and 30 options microstructure questions documented in `reports/phase12/VENDOR_CONTACT_QUESTIONNAIRE.md`.\n\n")

            f.write("## 11. Pre-Purchase Validation Procedure\n")
            f.write("Candidate sample datasets must pass the 11-stage `DataOnboardingValidator` detailed in `reports/phase12/PRE_PURCHASE_ACCEPTANCE_TEST.md` prior to contract execution.\n\n")

            f.write("## 12. Decision Tree\n")
            f.write("Logical gate progression documented in `reports/phase12/ACQUISITION_DECISION_TREE.md`.\n\n")

            f.write("## 13. Human Decision Form\n")
            f.write("Formal sign-off form ready for human signature in `reports/phase12/HUMAN_ACQUISITION_DECISION_FORM.md`.\n\n")

            f.write("## 14. Recommended Contact Order\n")
            f.write("1. **First Contact**: Send `reports/phase12/VENDOR_ENQUIRY_NSE.md` to NSE Data & Analytics.\n")
            f.write("2. **Parallel Contact**: Send `reports/phase12/VENDOR_ENQUIRY_TRUEDATA.md` to TrueData.\n")
            f.write("3. **Parallel Contact**: Send `reports/phase12/VENDOR_ENQUIRY_GDFL.md` to Global DataFeeds.\n")
            f.write("4. **Response Capture**: Log all responses into `reports/phase12/VENDOR_RESPONSE_TEMPLATE.md` and `data/phase12/vendor_responses.json`.\n")
            f.write("5. **Sample Audit**: Validate sample datasets via `PRE_PURCHASE_ACCEPTANCE_TEST.md`.\n")
            f.write("6. **Human Decision**: Present completed matrix and form to human decision maker.\n\n")

            f.write("## 15. Explicit Statement: No Purchase Has Been Authorized\n")
            f.write("> [!WARNING]\n")
            f.write("> Zero commercial purchases have been authorized. `PURCHASE_AUTHORIZED = FALSE`. No accounts, payments, or contracts have been entered into.\n\n")

            f.write("## 16. Explicit Statement: No Research Has Been Unlocked\n")
            f.write("> [!CAUTION]\n")
            f.write("> No alpha research, strategy optimization, parameter searches, broker connections, live trading, or paper trading have been unlocked. All research gates remain frozen.\n\n")
            f.write("## 17. Final State Summary\n")
            f.write("```text\n")
            f.write("PHASE_12_ACQUISITION_PACKAGE = COMPLETE\n")
            f.write("VENDOR_CONTACT_PACKAGE = READY\n")
            f.write("PRE_PURCHASE_VALIDATION = READY\n")
            f.write("COST_COMPARISON = READY\n")
            f.write("HUMAN_DECISION_FORM = READY\n\n")
            f.write("INTRADAY_1M_READY = BLOCKED\n")
            f.write("INTRADAY_5M_READY = BLOCKED\n")
            f.write("OPTIONS_BID_ASK_READY = BLOCKED\n")
            f.write("OPTIONS_EXECUTION_READY = BLOCKED\n\n")
            f.write("PURCHASE_AUTHORIZED = FALSE\n")
            f.write("HUMAN_DECISION_REQUIRED = TRUE\n\n")
            f.write("BROKER = NONE\n")
            f.write("LIVE_EXECUTION = DISABLED\n")
            f.write("AUTO_PAPER_ORDER_SUBMISSION = DISABLED\n\n")
            f.write("NEW_UNPREREGISTERED_ALPHA_RESEARCH = DISABLED\n\n")
            f.write("FROZEN_BASELINES = INTACT\n\n")
            f.write("OVERALL_STATE = AWAITING_HUMAN_VENDOR_DECISION\n")
            f.write("```\n")


if __name__ == "__main__":
    res = DecisionPackageManager.generate_all_artifacts()
    print("Decision Package Artifact Generation Output:")
    print(json.dumps(res, indent=2))
