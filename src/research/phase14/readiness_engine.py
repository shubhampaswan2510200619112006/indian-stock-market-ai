"""
Phase 14 Readiness Engine.

Evaluates dataset-scoped readiness, aggregate project-level readiness, and
capability-scoped research readiness:
- PROJECT_FULL_MARKET_DATA_READY
- INTRADAY_RESEARCH_CAPABILITY
- OPTIONS_EXECUTION_RESEARCH_CAPABILITY
- EQUITY_CROSS_SECTIONAL_RESEARCH_CAPABILITY

Strictly enforces:
TECHNICAL_DATA_CERTIFIED != RESEARCH_UNLOCKED
Does not perform research, optimize models, or unlock Phase 15.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from src.research.phase14.certifier import DatasetCertificationResult
from src.research.phase14.safety_policy import SafetyPolicy


class GateState(str, Enum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"
    NOT_ASSESSED = "NOT_ASSESSED"


@dataclass
class DatasetScopedReadinessResult:
    gate_name: str
    dataset_id: str
    underlying: str
    interval: str
    vendor: str
    state: GateState
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["state"] = self.state.value
        return d


@dataclass
class CapabilityReadinessResult:
    capability_name: str
    state: GateState
    required_gates: List[str]
    passed_gates: List[str]
    missing_gates: List[str]
    research_unlocked: bool = False  # Always False in Phase 14
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["state"] = self.state.value
        return d


@dataclass
class ResearchReadinessReport:
    assessment_timestamp: str
    aggregate_gates: Dict[str, str]
    dataset_scoped_results: List[DatasetScopedReadinessResult]
    capability_readiness: Dict[str, CapabilityReadinessResult]
    blocking_reasons: List[str]
    project_full_market_data_ready: str  # PASS / BLOCKED
    technical_data_certified: str  # PASS / BLOCKED
    phase_15_unlocked: bool = False  # Strictly False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessment_timestamp": self.assessment_timestamp,
            "aggregate_gates": self.aggregate_gates,
            "dataset_scoped_results": [r.to_dict() for r in self.dataset_scoped_results],
            "capability_readiness": {k: v.to_dict() for k, v in self.capability_readiness.items()},
            "blocking_reasons": self.blocking_reasons,
            "project_full_market_data_ready": self.project_full_market_data_ready,
            "technical_data_certified": self.technical_data_certified,
            "phase_15_unlocked": self.phase_15_unlocked,
        }


class Phase14ReadinessEngine:
    """
    Evaluates dataset-scoped and aggregate research readiness.
    """

    @classmethod
    def evaluate(
        cls,
        certification_results: List[DatasetCertificationResult],
    ) -> ResearchReadinessReport:
        SafetyPolicy.assert_safety_invariants(context="Phase14ReadinessEngine.evaluate")
        ts = datetime.now(timezone.utc).isoformat()

        scoped_results: List[DatasetScopedReadinessResult] = []
        blocking_reasons: List[str] = []

        # Filter out quarantined datasets
        valid_certs = [c for c in certification_results if not c.is_quarantined]

        # Dataset-scoped evaluations
        nifty_1m_certified = False
        banknifty_1m_certified = False
        nifty_5m_certified = False
        banknifty_5m_certified = False

        options_ltp_passed = False
        options_bid_ask_passed = False
        options_exec_passed = False

        provenance_all_passed = len(valid_certs) > 0
        license_all_passed = len(valid_certs) > 0

        for cert in valid_certs:
            u = cert.underlying.upper()
            inv = cert.interval.lower()

            # Intraday 1m
            if inv == "1m":
                is_ready = cert.is_certified and (cert.intraday_metrics is not None and cert.intraday_metrics.sessions_threshold_met)
                state = GateState.PASS if is_ready else GateState.BLOCKED
                scoped_results.append(
                    DatasetScopedReadinessResult(
                        gate_name="INTRADAY_1M_READY",
                        dataset_id=cert.dataset_id,
                        underlying=cert.underlying,
                        interval=cert.interval,
                        vendor=cert.vendor,
                        state=state,
                        reason="Validated >= 250 sessions" if is_ready else f"Blocked: {'; '.join(cert.rejection_reasons)}",
                    )
                )
                if is_ready:
                    if "BANK" in u:
                        banknifty_1m_certified = True
                    elif "NIFTY" in u:
                        nifty_1m_certified = True

            # Intraday 5m
            elif inv == "5m":
                is_ready = cert.is_certified and (cert.intraday_metrics is not None and cert.intraday_metrics.sessions_threshold_met)
                state = GateState.PASS if is_ready else GateState.BLOCKED
                scoped_results.append(
                    DatasetScopedReadinessResult(
                        gate_name="INTRADAY_5M_READY",
                        dataset_id=cert.dataset_id,
                        underlying=cert.underlying,
                        interval=cert.interval,
                        vendor=cert.vendor,
                        state=state,
                        reason="Validated >= 250 sessions" if is_ready else f"Blocked: {'; '.join(cert.rejection_reasons)}",
                    )
                )
                if is_ready:
                    if "BANK" in u:
                        banknifty_5m_certified = True
                    elif "NIFTY" in u:
                        nifty_5m_certified = True

            # Options
            if cert.options_metrics:
                # LTP ready
                if cert.options_metrics.options_quality_level in ["L1", "L2", "L3", "L4"]:
                    options_ltp_passed = True
                
                # Bid/Ask ready
                ba_ready = (cert.options_metrics.paired_quote_coverage_pct >= 50.0 and cert.options_metrics.crossed_quotes_count == 0)
                if ba_ready:
                    options_bid_ask_passed = True
                
                # Execution ready
                ex_ready = cert.options_metrics.continuity_threshold_met  # >= 70% continuous surface
                if ex_ready:
                    options_exec_passed = True

                scoped_results.append(
                    DatasetScopedReadinessResult(
                        gate_name="OPTIONS_BID_ASK_READY",
                        dataset_id=cert.dataset_id,
                        underlying=cert.underlying,
                        interval=cert.interval,
                        vendor=cert.vendor,
                        state=GateState.PASS if ba_ready else GateState.BLOCKED,
                        reason=f"Paired coverage {cert.options_metrics.paired_quote_coverage_pct}%",
                    )
                )
                scoped_results.append(
                    DatasetScopedReadinessResult(
                        gate_name="OPTIONS_EXECUTION_READY",
                        dataset_id=cert.dataset_id,
                        underlying=cert.underlying,
                        interval=cert.interval,
                        vendor=cert.vendor,
                        state=GateState.PASS if ex_ready else GateState.BLOCKED,
                        reason=f"Continuous surface {cert.options_metrics.continuous_executable_surface_pct}% (target >= 70%)",
                    )
                )

            # Check provenance / license per cert
            if cert.provenance_status != "VERIFIED":
                provenance_all_passed = False
            if cert.license_status not in ["LICENSE_VERIFIED", "COMMERCIAL_RESEARCH"]:
                license_all_passed = False

        # Aggregate Gate Derivation (Strictest criteria across required scope)
        intraday_1m_aggregate = (nifty_1m_certified and banknifty_1m_certified)
        intraday_5m_aggregate = (nifty_5m_certified and banknifty_5m_certified)

        if not nifty_1m_certified or not banknifty_1m_certified:
            missing_syms = []
            if not nifty_1m_certified:
                missing_syms.append("NIFTY 1m")
            if not banknifty_1m_certified:
                missing_syms.append("BANKNIFTY 1m")
            blocking_reasons.append(f"INTRADAY_1M_READY is BLOCKED: Missing certified datasets for {', '.join(missing_syms)}.")

        if not nifty_5m_certified or not banknifty_5m_certified:
            missing_syms = []
            if not nifty_5m_certified:
                missing_syms.append("NIFTY 5m")
            if not banknifty_5m_certified:
                missing_syms.append("BANKNIFTY 5m")
            blocking_reasons.append(f"INTRADAY_5M_READY is BLOCKED: Missing certified datasets for {', '.join(missing_syms)}.")

        if not options_bid_ask_passed:
            blocking_reasons.append("OPTIONS_BID_ASK_READY is BLOCKED: Lacks certified paired quote surface.")
        if not options_exec_passed:
            blocking_reasons.append("OPTIONS_EXECUTION_READY is BLOCKED: Lacks continuous paired surface >= 70%.")

        aggregate_gates = {
            "INTRADAY_1M_READY": GateState.PASS.value if intraday_1m_aggregate else GateState.BLOCKED.value,
            "INTRADAY_5M_READY": GateState.PASS.value if intraday_5m_aggregate else GateState.BLOCKED.value,
            "OPTIONS_LTP_READY": GateState.PASS.value if options_ltp_passed else GateState.BLOCKED.value,
            "OPTIONS_BID_ASK_READY": GateState.PASS.value if options_bid_ask_passed else GateState.BLOCKED.value,
            "OPTIONS_EXECUTION_READY": GateState.PASS.value if options_exec_passed else GateState.BLOCKED.value,
            "PROVENANCE_READY": GateState.PASS.value if provenance_all_passed else GateState.BLOCKED.value,
            "LICENSE_READY": GateState.PASS.value if license_all_passed else GateState.BLOCKED.value,
            "DATA_QUALITY_READY": GateState.PASS.value if (provenance_all_passed and license_all_passed) else GateState.BLOCKED.value,
        }

        # Capability-Scoped Research Readiness (Correction 1)
        # 1. INTRADAY_RESEARCH_CAPABILITY: requires INTRADAY_1M_READY, INTRADAY_5M_READY, PROVENANCE_READY, LICENSE_READY
        intraday_reqs = ["INTRADAY_1M_READY", "INTRADAY_5M_READY", "PROVENANCE_READY", "LICENSE_READY"]
        intraday_passed_reqs = [g for g in intraday_reqs if aggregate_gates.get(g) == GateState.PASS.value]
        intraday_missing_reqs = [g for g in intraday_reqs if aggregate_gates.get(g) != GateState.PASS.value]
        intraday_cap_state = GateState.PASS if len(intraday_missing_reqs) == 0 else GateState.BLOCKED

        # 2. OPTIONS_EXECUTION_RESEARCH_CAPABILITY: requires OPTIONS_BID_ASK_READY, OPTIONS_EXECUTION_READY, PROVENANCE_READY, LICENSE_READY
        options_reqs = ["OPTIONS_BID_ASK_READY", "OPTIONS_EXECUTION_READY", "PROVENANCE_READY", "LICENSE_READY"]
        options_passed_reqs = [g for g in options_reqs if aggregate_gates.get(g) == GateState.PASS.value]
        options_missing_reqs = [g for g in options_reqs if aggregate_gates.get(g) != GateState.PASS.value]
        options_cap_state = GateState.PASS if len(options_missing_reqs) == 0 else GateState.BLOCKED

        # 3. EQUITY_CROSS_SECTIONAL_RESEARCH_CAPABILITY: evaluated based on Phase 10/11 constituent integrity
        equity_cap_state = GateState.BLOCKED  # Commercial tick constituent archive unacquired

        # 4. PROJECT_FULL_MARKET_DATA_READY: all gates must pass
        all_gates_pass = (
            intraday_1m_aggregate
            and intraday_5m_aggregate
            and options_bid_ask_passed
            and options_exec_passed
            and provenance_all_passed
            and license_all_passed
        )
        project_full_ready = GateState.PASS.value if all_gates_pass else GateState.BLOCKED.value
        tech_certified = GateState.PASS.value if (len(valid_certs) > 0 and all(c.is_certified for c in valid_certs)) else GateState.BLOCKED.value

        capabilities = {
            "INTRADAY_RESEARCH_CAPABILITY": CapabilityReadinessResult(
                capability_name="INTRADAY_RESEARCH_CAPABILITY",
                state=intraday_cap_state,
                required_gates=intraday_reqs,
                passed_gates=intraday_passed_reqs,
                missing_gates=intraday_missing_reqs,
                research_unlocked=False,
                details="Requires NIFTY/BANKNIFTY 1m and 5m certified datasets with valid license",
            ),
            "OPTIONS_EXECUTION_RESEARCH_CAPABILITY": CapabilityReadinessResult(
                capability_name="OPTIONS_EXECUTION_RESEARCH_CAPABILITY",
                state=options_cap_state,
                required_gates=options_reqs,
                passed_gates=options_passed_reqs,
                missing_gates=options_missing_reqs,
                research_unlocked=False,
                details="Requires continuous paired Bid/Ask surface >= 70.0% with valid license",
            ),
            "EQUITY_CROSS_SECTIONAL_RESEARCH_CAPABILITY": CapabilityReadinessResult(
                capability_name="EQUITY_CROSS_SECTIONAL_RESEARCH_CAPABILITY",
                state=equity_cap_state,
                required_gates=["EQUITY_HISTORY_READY", "CONSTITUENT_PIT_READY"],
                passed_gates=[],
                missing_gates=["EQUITY_HISTORY_READY", "CONSTITUENT_PIT_READY"],
                research_unlocked=False,
                details="Requires clean survivorship-free constituent adjusted history",
            ),
        }

        return ResearchReadinessReport(
            assessment_timestamp=ts,
            aggregate_gates=aggregate_gates,
            dataset_scoped_results=scoped_results,
            capability_readiness=capabilities,
            blocking_reasons=blocking_reasons,
            project_full_market_data_ready=project_full_ready,
            technical_data_certified=tech_certified,
            phase_15_unlocked=False,
        )
