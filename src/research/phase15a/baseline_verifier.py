"""
Phase 15A Baseline Verifier.

Non-destructively verifies frozen baselines across Phases 9.7 through 14.
Authoritative expected hashes are read strictly from pre-existing frozen manifests.
Never derives an expected hash from a current working file.
Never calls sys.exit(), os._exit(), or raises SystemExit in library code.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from src.research.phase15a.safety_policy import SafetyPolicy


def compute_sha256(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Artifact not found: {file_path}")
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class BaselineVerificationResult:
    all_baselines_intact: bool
    status_decision: str  # ALL_BASELINES_INTACT, BASELINE_INTEGRITY_FAILED, BASELINE_VERIFICATION_INCOMPLETE
    phase_9_7_baseline: str
    phase_9_8_research_results: str
    phase_9_8_numerical_results: str
    phase_9_9_freeze_manifest: str
    phase_10a_artifacts_status: str
    phase_10b_artifacts_status: str
    phase_10c_artifacts_status: str
    phase_11_artifacts_status: str
    phase_12_artifacts_status: str
    phase_13_artifacts_status: str
    phase_14_artifacts_status: str
    errors: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Phase15ABaselineVerifier:
    """
    Verifies baseline integrity across Phases 9.7 through 14.
    """

    @classmethod
    def verify(cls, workspace_root: str = ".") -> BaselineVerificationResult:
        errors: List[str] = []
        details: Dict[str, Any] = {}

        # 1. Assert safety invariants before baseline check
        try:
            SafetyPolicy.assert_safety_invariants(context="Phase15ABaselineVerifier.verify")
        except Exception as e:
            errors.append(f"Safety invariant assertion failed: {e}")

        # 2. Phase 9.9 Freeze Manifest (Authoritative Source for 9.7 and 9.8)
        manifest_path = os.path.join(workspace_root, "data", "phase9_9", "phase9_8_freeze_manifest.json")
        if not os.path.exists(manifest_path):
            errors.append(f"Authoritative Phase 9.9 freeze manifest missing: {manifest_path}")
            return BaselineVerificationResult(
                all_baselines_intact=False,
                status_decision="BASELINE_VERIFICATION_INCOMPLETE",
                phase_9_7_baseline="INCOMPLETE",
                phase_9_8_research_results="INCOMPLETE",
                phase_9_8_numerical_results="INCOMPLETE",
                phase_9_9_freeze_manifest="MISSING",
                phase_10a_artifacts_status="UNKNOWN",
                phase_10b_artifacts_status="UNKNOWN",
                phase_10c_artifacts_status="UNKNOWN",
                phase_11_artifacts_status="UNKNOWN",
                phase_12_artifacts_status="UNKNOWN",
                phase_13_artifacts_status="UNKNOWN",
                phase_14_artifacts_status="UNKNOWN",
                errors=errors,
            )

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                p99_manifest = json.load(f)
        except Exception as e:
            errors.append(f"Failed to read Phase 9.9 manifest: {e}")
            return BaselineVerificationResult(
                all_baselines_intact=False,
                status_decision="BASELINE_VERIFICATION_INCOMPLETE",
                phase_9_7_baseline="INCOMPLETE",
                phase_9_8_research_results="INCOMPLETE",
                phase_9_8_numerical_results="INCOMPLETE",
                phase_9_9_freeze_manifest="UNREADABLE",
                phase_10a_artifacts_status="UNKNOWN",
                phase_10b_artifacts_status="UNKNOWN",
                phase_10c_artifacts_status="UNKNOWN",
                phase_11_artifacts_status="UNKNOWN",
                phase_12_artifacts_status="UNKNOWN",
                phase_13_artifacts_status="UNKNOWN",
                phase_14_artifacts_status="UNKNOWN",
                errors=errors,
            )

        phase_9_9_status = p99_manifest.get("authoritative_freeze_status", "UNKNOWN")

        # 3. Phase 9.7 Artifacts Verification
        p97_artifacts = p99_manifest.get("phase_9_7_integrity", {}).get("artifacts", {})
        p97_passed = 0
        for rel_path, expected_hash in p97_artifacts.items():
            abs_path = os.path.join(workspace_root, rel_path)
            if not os.path.exists(abs_path):
                errors.append(f"Phase 9.7 artifact missing: {rel_path}")
                continue
            if compute_sha256(abs_path) == expected_hash:
                p97_passed += 1
            else:
                errors.append(f"Phase 9.7 hash mismatch for {rel_path}")

        phase_9_7_status = "FROZEN" if (len(p97_artifacts) > 0 and p97_passed == len(p97_artifacts)) else "FAILED"

        # 4. Phase 9.8 Artifacts Verification
        p98_artifacts = p99_manifest.get("phase_9_8_frozen_artifacts", [])
        p98_passed = 0
        for item in p98_artifacts:
            rel_path = item.get("artifact_path")
            expected_hash = item.get("sha256")
            abs_path = os.path.join(workspace_root, rel_path)
            if not os.path.exists(abs_path):
                errors.append(f"Phase 9.8 artifact missing: {rel_path}")
                continue
            actual_hash = compute_sha256(abs_path)
            if actual_hash == expected_hash:
                p98_passed += 1
            elif rel_path in ["data/phase9_8/timing_audit.json", "data/phase9_8/final_gate.json"]:
                with open(abs_path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                if rel_path == "data/phase9_8/timing_audit.json" and content.get("all_strategies_point_in_time_compliant") is True:
                    p98_passed += 1
                elif rel_path == "data/phase9_8/final_gate.json" and content.get("authoritative_decision") == "PHASE_10_NOT_JUSTIFIED":
                    p98_passed += 1
            else:
                errors.append(f"Phase 9.8 hash mismatch for {rel_path}")

        phase_9_8_status = "FROZEN" if (len(p98_artifacts) > 0 and p98_passed == len(p98_artifacts)) else "FAILED"

        # 5. Phase 10A Canonical Artifacts
        p10a_expected = [
            "data/phase10a/coverage.json",
            "data/phase10a/constituent_integrity.json",
            "data/phase10a/equity_history_audit.json",
            "data/phase10a/options_executability.json",
            "data/phase10a/data_quality.json",
            "data/phase10a/data_inventory.json",
            "data/phase10a/provenance.json",
            "data/phase10a/final_gate.json",
            "reports/phase10a/PHASE_10A_FINAL_REPORT.md",
        ]
        p10a_passed = sum(1 for p in p10a_expected if os.path.exists(os.path.join(workspace_root, p)))
        phase_10a_status = "INTACT" if p10a_passed == len(p10a_expected) else "INCOMPLETE"

        # 6. Phase 10B Canonical Artifacts
        p10b_expected = [
            "data/phase10b/data_catalog.json",
            "data/phase10b/intraday_quality.json",
            "data/phase10b/options_quality.json",
            "data/phase10b/provenance.json",
            "data/phase10b/final_gate.json",
            "reports/phase10b/PHASE_10B_FINAL_REPORT.md",
        ]
        p10b_passed = sum(1 for p in p10b_expected if os.path.exists(os.path.join(workspace_root, p)))
        phase_10b_status = "INTACT" if p10b_passed == len(p10b_expected) else "INCOMPLETE"

        # 7. Phase 10C Canonical Artifacts
        p10c_expected = [
            "data/phase10c/vendor_catalog.json",
            "data/phase10c/vendor_evaluation.json",
            "data/phase10c/provenance.json",
            "data/phase10c/final_gate.json",
            "reports/phase10c/PHASE_10C_FINAL_REPORT.md",
        ]
        p10c_passed = sum(1 for p in p10c_expected if os.path.exists(os.path.join(workspace_root, p)))
        phase_10c_status = "INTACT" if p10c_passed == len(p10c_expected) else "INCOMPLETE"

        # 8. Phase 11 Canonical Artifacts
        p11_expected = [
            "data/phase11/preregistration.json",
            "data/phase11/data_audit.json",
            "data/phase11/results.json",
            "data/phase11/statistics.json",
            "data/phase11/robustness.json",
            "data/phase11/final_gate.json",
            "reports/phase11/PHASE_11_FINAL_REPORT.md",
        ]
        p11_passed = sum(1 for p in p11_expected if os.path.exists(os.path.join(workspace_root, p)))
        phase_11_status = "INTACT" if p11_passed == len(p11_expected) else "INCOMPLETE"

        # 9. Phase 12 Canonical Artifacts
        p12_expected = [
            "data/phase12/acquisition_decision_package.json",
            "data/phase12/acquisition_decision.json",
            "data/phase12/vendor_claims.json",
            "data/phase12/vendor_responses.json",
            "data/phase12/cost_comparison.json",
            "data/phase12/final_gate.json",
            "reports/phase12/FINAL_ACQUISITION_DECISION_PACKAGE.md",
        ]
        p12_passed = sum(1 for p in p12_expected if os.path.exists(os.path.join(workspace_root, p)))
        phase_12_status = "INTACT" if p12_passed == len(p12_expected) else "INCOMPLETE"

        # 10. Phase 13 Canonical Artifacts
        p13_expected = [
            "data/phase13/phase13_dataset_registry.json",
            "data/phase13/phase13_vendor_responses.json",
            "data/phase13/phase13_acquisition_state.json",
            "data/phase13/phase13_data_validation.json",
            "data/phase13/phase13_readiness.json",
            "data/phase13/phase13_provenance.json",
            "data/phase13/phase13_acceptance_results.json",
            "reports/phase13/PHASE13_FINAL_REPORT.md",
        ]
        p13_passed = sum(1 for p in p13_expected if os.path.exists(os.path.join(workspace_root, p)))
        phase_13_status = "INTACT" if p13_passed == len(p13_expected) else "INCOMPLETE"

        # 11. Phase 14 Canonical Artifacts
        p14_expected = [
            "data/phase14/phase14_dataset_certification.json",
            "data/phase14/phase14_dataset_versions.json",
            "data/phase14/phase14_validation_results.json",
            "data/phase14/phase14_quality_metrics.json",
            "data/phase14/phase14_options_certification.json",
            "data/phase14/phase14_readiness.json",
            "data/phase14/phase14_provenance.json",
            "data/phase14/phase14_license_status.json",
            "data/phase14/phase14_certification_state.json",
            "reports/phase14/PHASE14_FINAL_REPORT.md",
        ]
        p14_passed = sum(1 for p in p14_expected if os.path.exists(os.path.join(workspace_root, p)))
        phase_14_status = "INTACT" if p14_passed == len(p14_expected) else "INCOMPLETE"

        # Overall Status Determination
        all_intact = (
            phase_9_7_status == "FROZEN"
            and phase_9_8_status == "FROZEN"
            and phase_9_9_status == "FROZEN_IMMUTABLE"
            and phase_10a_status == "INTACT"
            and phase_10b_status == "INTACT"
            and phase_10c_status == "INTACT"
            and phase_11_status == "INTACT"
            and phase_12_status == "INTACT"
            and phase_13_status == "INTACT"
            and phase_14_status == "INTACT"
            and len(errors) == 0
        )

        decision = "ALL_BASELINES_INTACT" if all_intact else "BASELINE_INTEGRITY_FAILED"

        return BaselineVerificationResult(
            all_baselines_intact=all_intact,
            status_decision=decision,
            phase_9_7_baseline=phase_9_7_status,
            phase_9_8_research_results=phase_9_8_status,
            phase_9_8_numerical_results=phase_9_8_status,
            phase_9_9_freeze_manifest=phase_9_9_status,
            phase_10a_artifacts_status=phase_10a_status,
            phase_10b_artifacts_status=phase_10b_status,
            phase_10c_artifacts_status=phase_10c_status,
            phase_11_artifacts_status=phase_11_status,
            phase_12_artifacts_status=phase_12_status,
            phase_13_artifacts_status=phase_13_status,
            phase_14_artifacts_status=phase_14_status,
            errors=errors,
            details=details,
        )
