"""
Phase 14 Data Quality Scorecard.

Generates a deterministic diagnostic scorecard across 11 dimensions:
PROVENANCE, LICENSE, SCHEMA, TIMESTAMP, SESSION_COVERAGE, BAR_COMPLETENESS,
OHLC_INTEGRITY, HISTORICAL_DEPTH, CROSS_INSTRUMENT_COVERAGE,
OPTIONS_QUOTE_VALIDITY, OPTIONS_EXECUTABLE_SURFACE.

Enforces:
DATA_QUALITY_SCORE = DIAGNOSTIC_ONLY
The scorecard summarizes diagnostics but NEVER overrides hard certification gates.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from src.research.phase14.certifier import DatasetCertificationResult


@dataclass
class QualityDimensionScore:
    dimension_name: str
    status: str  # PASS, FAIL, BLOCKED, NOT_APPLICABLE
    diagnostic_score: float  # 0.0 to 100.0 (DIAGNOSTIC ONLY)
    hard_gate_passed: bool
    details: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QualityScorecardReport:
    scorecard_id: str
    dataset_id: str
    version_id: str
    overall_diagnostic_score: float
    scorecard_policy: str = "DIAGNOSTIC_ONLY"
    hard_gates_intact: bool = False
    certification_eligible_by_gates: bool = False
    dimensions: List[QualityDimensionScore] = field(default_factory=list)
    blocking_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["dimensions"] = [dim.to_dict() for dim in self.dimensions]
        return d


class Phase14QualityScorecard:
    """
    Evaluates dataset quality dimensions strictly for diagnostic and reporting purposes.
    Hard gates can never be overridden by numeric scores.
    """

    POLICY = "DIAGNOSTIC_ONLY"

    @classmethod
    def evaluate(cls, cert_result: DatasetCertificationResult) -> QualityScorecardReport:
        dimensions: List[QualityDimensionScore] = []
        blocking_reasons: List[str] = []

        # 1. PROVENANCE
        prov_passed = (cert_result.provenance_status == "VERIFIED")
        dimensions.append(
            QualityDimensionScore(
                dimension_name="PROVENANCE",
                status="PASS" if prov_passed else "FAIL",
                diagnostic_score=100.0 if prov_passed else 0.0,
                hard_gate_passed=prov_passed,
                details=f"Source artifact: {cert_result.provenance_status}",
            )
        )
        if not prov_passed:
            blocking_reasons.append("PROVENANCE_READY is BLOCKED: Source artifact not verified.")

        # 2. LICENSE
        lic_passed = (cert_result.license_status in ["LICENSE_VERIFIED", "COMMERCIAL_RESEARCH"])
        dimensions.append(
            QualityDimensionScore(
                dimension_name="LICENSE",
                status="PASS" if lic_passed else "BLOCKED",
                diagnostic_score=100.0 if lic_passed else (50.0 if cert_result.license_status == "LICENSE_RESTRICTED" else 0.0),
                hard_gate_passed=lic_passed,
                details=f"Status: {cert_result.license_status}",
            )
        )
        if not lic_passed:
            blocking_reasons.append(f"LICENSE_READY is BLOCKED: License status '{cert_result.license_status}' unconfirmed for research.")

        # 3. SCHEMA
        schema_passed = ("4. SCHEMA" in cert_result.stages_passed)
        dimensions.append(
            QualityDimensionScore(
                dimension_name="SCHEMA",
                status="PASS" if schema_passed else "FAIL",
                diagnostic_score=100.0 if schema_passed else 0.0,
                hard_gate_passed=schema_passed,
                details="Required schema columns verified",
            )
        )

        # 4. TIMESTAMP
        ts_passed = ("5. TIMESTAMP" in cert_result.stages_passed)
        dimensions.append(
            QualityDimensionScore(
                dimension_name="TIMESTAMP",
                status="PASS" if ts_passed else "FAIL",
                diagnostic_score=100.0 if ts_passed else 0.0,
                hard_gate_passed=ts_passed,
                details="Monotonic chronological IST timestamp integrity",
            )
        )

        # 5. SESSION_COVERAGE
        sess_passed = (cert_result.intraday_metrics.sessions_threshold_met if cert_result.intraday_metrics else True)
        valid_sess = cert_result.intraday_metrics.valid_trading_sessions if cert_result.intraday_metrics else 0
        sess_score = min(100.0, round((valid_sess / 250.0) * 100.0, 1)) if cert_result.intraday_metrics else 100.0
        dimensions.append(
            QualityDimensionScore(
                dimension_name="SESSION_COVERAGE",
                status="PASS" if sess_passed else "FAIL",
                diagnostic_score=sess_score,
                hard_gate_passed=sess_passed,
                details=f"Observed {valid_sess} valid sessions (target: >= 250)",
            )
        )
        if not sess_passed:
            blocking_reasons.append(f"INSUFFICIENT_SESSIONS: {valid_sess} < 250 sessions.")

        # 6. BAR_COMPLETENESS
        bar_passed = ("7. SESSION COMPLETENESS" in cert_result.stages_passed) if cert_result.intraday_metrics else True
        dimensions.append(
            QualityDimensionScore(
                dimension_name="BAR_COMPLETENESS",
                status="PASS" if bar_passed else "FAIL",
                diagnostic_score=95.0 if bar_passed else 40.0,
                hard_gate_passed=bar_passed,
                details="Session bar completeness evaluated",
            )
        )

        # 7. OHLC_INTEGRITY
        ohlc_passed = ("6. OHLC INTEGRITY" in cert_result.stages_passed)
        dimensions.append(
            QualityDimensionScore(
                dimension_name="OHLC_INTEGRITY",
                status="PASS" if ohlc_passed else "FAIL",
                diagnostic_score=100.0 if ohlc_passed else 0.0,
                hard_gate_passed=ohlc_passed,
                details=f"Violations: {cert_result.intraday_metrics.ohlc_violations_count if cert_result.intraday_metrics else 0}",
            )
        )

        # 8. HISTORICAL_DEPTH
        depth_val = cert_result.options_metrics.depth_verification_level if cert_result.options_metrics else "NOT_APPLICABLE"
        dimensions.append(
            QualityDimensionScore(
                dimension_name="HISTORICAL_DEPTH",
                status="PASS" if depth_val == "HISTORICAL_DEPTH_VERIFIED" else "DIAGNOSTIC",
                diagnostic_score=100.0 if depth_val == "HISTORICAL_DEPTH_VERIFIED" else 20.0,
                hard_gate_passed=True,  # Non-blocking unless explicitly required
                details=f"Depth level: {depth_val}",
            )
        )

        # 9. CROSS_INSTRUMENT_COVERAGE
        dimensions.append(
            QualityDimensionScore(
                dimension_name="CROSS_INSTRUMENT_COVERAGE",
                status="PASS",
                diagnostic_score=100.0,
                hard_gate_passed=True,
                details=f"Instrument scoped: {cert_result.underlying} {cert_result.interval}",
            )
        )

        # 10. OPTIONS_QUOTE_VALIDITY
        opt_quote_passed = (cert_result.options_metrics.crossed_quotes_count == 0) if cert_result.options_metrics else True
        dimensions.append(
            QualityDimensionScore(
                dimension_name="OPTIONS_QUOTE_VALIDITY",
                status="PASS" if opt_quote_passed else "FAIL",
                diagnostic_score=100.0 if opt_quote_passed else 0.0,
                hard_gate_passed=opt_quote_passed,
                details="Crossed market checks evaluated",
            )
        )

        # 11. OPTIONS_EXECUTABLE_SURFACE
        cont_passed = (cert_result.options_metrics.continuity_threshold_met) if cert_result.options_metrics else True
        cont_pct = cert_result.options_metrics.continuous_executable_surface_pct if cert_result.options_metrics else 100.0
        dimensions.append(
            QualityDimensionScore(
                dimension_name="OPTIONS_EXECUTABLE_SURFACE",
                status="PASS" if cont_passed else "FAIL",
                diagnostic_score=cont_pct,
                hard_gate_passed=cont_passed,
                details=f"Continuous surface: {cont_pct}% (target >= 70.0%)",
            )
        )
        if not cont_passed:
            blocking_reasons.append(f"CONTINUOUS_EXECUTABLE_SURFACE_LOW: {cont_pct}% < 70.0% threshold.")

        # Compute average diagnostic score
        scores = [d.diagnostic_score for d in dimensions]
        overall_score = round(sum(scores) / max(1, len(scores)), 2)

        # Hard gate enforcement: ANY failed hard gate prevents certification regardless of score
        all_hard_gates_passed = all(d.hard_gate_passed for d in dimensions)
        cert_eligible = all_hard_gates_passed and cert_result.is_certified

        return QualityScorecardReport(
            scorecard_id=f"SCORE-{cert_result.dataset_id}",
            dataset_id=cert_result.dataset_id,
            version_id=cert_result.version_id,
            overall_diagnostic_score=overall_score,
            scorecard_policy=cls.POLICY,
            hard_gates_intact=all_hard_gates_passed,
            certification_eligible_by_gates=cert_eligible,
            dimensions=dimensions,
            blocking_reasons=blocking_reasons,
        )
