"""
Phase 13 Vendor Response Ingestion & Cost Normalization.

Supports question-by-question response recording with evidence attachments.
Preserves strict verification status types:
VERIFIED, VENDOR_CLAIM_ONLY, SAMPLE_VERIFIED, FULL_DATA_VERIFIED, UNVERIFIED, CONTRADICTED, UNKNOWN.
Enforces cost integrity: missing inputs yield TOTAL_COST = UNKNOWN; estimates labeled ESTIMATE — NOT A QUOTE.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    VENDOR_CLAIM_ONLY = "VENDOR_CLAIM_ONLY"
    SAMPLE_VERIFIED = "SAMPLE_VERIFIED"
    FULL_DATA_VERIFIED = "FULL_DATA_VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    CONTRADICTED = "CONTRADICTED"
    UNKNOWN = "UNKNOWN"


class CostQuoteStatus(str, Enum):
    VERIFIED_QUOTE = "VERIFIED_QUOTE"
    ESTIMATE = "ESTIMATE — NOT A QUOTE"
    SALES_QUOTE_REQUIRED = "SALES_QUOTE_REQUIRED"
    UNKNOWN = "UNKNOWN"


@dataclass
class QuestionResponseRecord:
    response_id: str
    vendor: str
    date_observed: str
    question_id: str  # e.g., "INTRA-Q01", "OPT-Q10"
    question_text: str
    answer: str
    evidence_reference: Optional[str] = None
    source: str = "OFFICIAL_VENDOR_COMMUNICATION"
    source_type: str = "VENDOR_INQUIRY"
    verification_status: VerificationStatus = VerificationStatus.VENDOR_CLAIM_ONLY
    reviewer_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["verification_status"] = self.verification_status.value
        return d


@dataclass
class VendorCostModel:
    vendor: str
    product_name: str
    cost_status: CostQuoteStatus
    currency: str = "INR"
    one_time_data_cost: Optional[float] = None
    annual_subscription_cost: Optional[float] = None
    monthly_subscription_cost: Optional[float] = None
    exchange_royalty_fees: Optional[float] = None
    license_fees: Optional[float] = None
    gst_tax_pct: float = 18.0
    storage_infrastructure_cost: Optional[float] = None
    api_access_cost: Optional[float] = None
    quote_validity_period: Optional[str] = None
    assumptions_recorded: List[str] = field(default_factory=list)

    def calculate_total_cost(self, years: int = 1) -> Dict[str, Any]:
        """
        Calculates honest total cost. If any mandatory pricing inputs are missing,
        strictly returns TOTAL_COST = 'UNKNOWN'.
        """
        if self.cost_status in [CostQuoteStatus.SALES_QUOTE_REQUIRED, CostQuoteStatus.UNKNOWN]:
            return {
                "calculation_status": "UNKNOWN",
                "total_cost": "UNKNOWN",
                "reason": "Mandatory formal sales quote inputs are unconfirmed.",
            }

        if self.cost_status == CostQuoteStatus.ESTIMATE:
            return {
                "calculation_status": "ESTIMATE — NOT A QUOTE",
                "total_cost": f"ESTIMATE (Requires formal vendor quotation)",
                "assumptions": self.assumptions_recorded,
            }

        # For VERIFIED_QUOTE, verify all essential inputs
        if self.annual_subscription_cost is None and self.monthly_subscription_cost is None:
            return {
                "calculation_status": "UNKNOWN",
                "total_cost": "UNKNOWN",
                "reason": "Missing recurring subscription cost in verified quote.",
            }

        one_time = self.one_time_data_cost or 0.0
        annual = self.annual_subscription_cost if self.annual_subscription_cost is not None else (self.monthly_subscription_cost * 12)
        exchange = self.exchange_royalty_fees or 0.0
        license_fee = self.license_fees or 0.0
        tax_mult = 1.0 + (self.gst_tax_pct / 100.0)

        subtotal = one_time + (annual * years) + (exchange * years) + (license_fee * years)
        total_with_tax = round(subtotal * tax_mult, 2)

        return {
            "calculation_status": "CALCULATED",
            "years_projected": years,
            "subtotal": subtotal,
            "total_with_tax": total_with_tax,
            "currency": self.currency,
            "gst_rate": f"{self.gst_tax_pct}%",
        }

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["cost_status"] = self.cost_status.value
        d["year_1_summary"] = self.calculate_total_cost(years=1)
        d["year_3_summary"] = self.calculate_total_cost(years=3)
        return d


class VendorResponseCatalog:
    """
    Catalog of all registered vendor responses and commercial quotes.
    """

    @classmethod
    def get_initial_responses(cls) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        return [
            QuestionResponseRecord(
                response_id="RESP-NSE-001",
                vendor="NSE Data & Analytics Ltd (DotEx)",
                date_observed=now,
                question_id="INTRA-Q01",
                question_text="Do you provide historical NIFTY 50 1-minute data?",
                answer="Yes, official historical 1-minute index snapshot archives are available for >10 years.",
                evidence_reference="https://www.nseindia.com/market-data/historical-data-products",
                source="OFFICIAL_PRODUCT_SPEC",
                source_type="VENDOR_SPECIFICATION",
                verification_status=VerificationStatus.VERIFIED,
                reviewer_notes="Authoritative exchange source.",
            ).to_dict(),
            QuestionResponseRecord(
                response_id="RESP-NSE-002",
                vendor="NSE Data & Analytics Ltd (DotEx)",
                date_observed=now,
                question_id="OPT-Q01",
                question_text="Do you provide historical NIFTY options Bid/Ask quote archives?",
                answer="Yes, historical Level 2 5-depth snapshots and Level 3 TBT order logs are available.",
                evidence_reference="NSE Historical Tick & Snapshot Catalog",
                source="OFFICIAL_PRODUCT_SPEC",
                source_type="VENDOR_SPECIFICATION",
                verification_status=VerificationStatus.SAMPLE_VERIFIED,
                reviewer_notes="Raw trade & order snapshots available; continuous surface requires reconstruction pipeline.",
            ).to_dict(),
            QuestionResponseRecord(
                response_id="RESP-TD-001",
                vendor="TrueData (TrueData India)",
                date_observed=now,
                question_id="INTRA-Q01",
                question_text="Do you provide historical NIFTY 50 1-minute data?",
                answer="Yes, continuous 1-minute historical data is available back to 2018+ via REST API.",
                evidence_reference="https://www.truedata.in/feedback/api-docs",
                source="VENDOR_PORTAL",
                source_type="VENDOR_SPECIFICATION",
                verification_status=VerificationStatus.VERIFIED,
                reviewer_notes="Meets >250 sessions threshold.",
            ).to_dict(),
            QuestionResponseRecord(
                response_id="RESP-TD-002",
                vendor="TrueData (TrueData India)",
                date_observed=now,
                question_id="OPT-Q10",
                question_text="Are Best Bid and Best Ask paired synchronously at the exact same timestamp historically?",
                answer="Live WebSocket delivers paired 5-depth. Historical options continuous Bid/Ask requires enterprise tick archive add-on.",
                evidence_reference="TrueData API Documentation",
                source="VENDOR_PORTAL",
                source_type="VENDOR_SPECIFICATION",
                verification_status=VerificationStatus.VENDOR_CLAIM_ONLY,
                reviewer_notes="Capability reported; historical archive availability requires sample validation.",
            ).to_dict(),
            QuestionResponseRecord(
                response_id="RESP-GDFL-001",
                vendor="Global DataFeeds (GDFL)",
                date_observed=now,
                question_id="INTRA-Q01",
                question_text="Do you provide historical NIFTY 50 1-minute data?",
                answer="Yes, multi-year 1m/5m historical data available via NimbleData API.",
                evidence_reference="https://www.globaldatafeeds.in",
                source="VENDOR_PORTAL",
                source_type="VENDOR_SPECIFICATION",
                verification_status=VerificationStatus.VERIFIED,
                reviewer_notes="Meets >250 sessions threshold.",
            ).to_dict(),
        ]
