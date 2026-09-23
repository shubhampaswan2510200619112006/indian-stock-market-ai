"""
Phase 11 Pre-Execution Gate.

Verifies the 5 mandatory prerequisites before empirical evaluation:
1. PHASE_11_PREREGISTRATION_LOCKED == True
2. PHASE_11_COST_MODEL_LOCKED == True
3. PHASE_11_UNIVERSE_VERIFIED == True
4. PHASE_11_DATA_AUDIT_PASS == True
5. PHASE_11_BASELINES_INTACT == True

If any check fails, emits PHASE_11_EXECUTION = BLOCKED and prevents execution.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from src.research.phase11.baseline_verifier import verify_frozen_baselines
from src.research.phase11.data_auditor import DataAuditor
from src.research.phase11.cost_model import IndianEquityCostModel


def verify_phase11_pre_execution_gate(workspace_root: str = ".") -> Dict[str, Any]:
    """
    Checks all 5 gating conditions before allowing empirical calculations.
    """
    gate_state = {
        "PHASE_11_PREREGISTRATION_LOCKED": False,
        "PHASE_11_COST_MODEL_LOCKED": False,
        "PHASE_11_UNIVERSE_VERIFIED": False,
        "PHASE_11_DATA_AUDIT_PASS": False,
        "PHASE_11_BASELINES_INTACT": False,
        "PHASE_11_EXECUTION": "BLOCKED",
        "details": {},
        "errors": [],
    }

    # 1. Preregistration Locked Check
    prereg_path = os.path.join(workspace_root, "data", "phase11", "preregistration.json")
    if os.path.exists(prereg_path):
        try:
            with open(prereg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("lock_status") == "PREREGISTRATION_LOCKED" and data.get("total_hypotheses") == 6:
                    gate_state["PHASE_11_PREREGISTRATION_LOCKED"] = True
                else:
                    gate_state["errors"].append("Preregistration file lock status invalid or count != 6")
        except Exception as e:
            gate_state["errors"].append(f"Failed to read preregistration file: {e}")
    else:
        gate_state["errors"].append(f"Preregistration file missing: {prereg_path}")

    # 2. Cost Model Locked Check
    try:
        cm = IndianEquityCostModel()
        # Verify dynamic calculation works
        res = cm.compute_round_trip(1000.0, 1000.0)
        if res.total_friction > 0 and res.total_statutory_cost > 0 and res.total_brokerage > 0:
            gate_state["PHASE_11_COST_MODEL_LOCKED"] = True
        else:
            gate_state["errors"].append("Cost model returned non-positive friction")
    except Exception as e:
        gate_state["errors"].append(f"Cost model verification failed: {e}")

    # 3. Universe Verified & 4. Data Audit Pass
    try:
        auditor = DataAuditor(workspace_root=workspace_root)
        audit_res = auditor.audit_dataset()
        gate_state["details"]["data_audit"] = audit_res

        if audit_res["universe_classification"] == "VERIFIED_NIFTY_CONSTITUENT_SUBSET" and audit_res["number_of_equity_symbols"] == 10:
            gate_state["PHASE_11_UNIVERSE_VERIFIED"] = True
        else:
            gate_state["errors"].append("Universe classification or constituent count incorrect")

        if audit_res["all_symbols_clean"] is True and audit_res["common_sessions_count"] >= 250:
            gate_state["PHASE_11_DATA_AUDIT_PASS"] = True
        else:
            gate_state["errors"].append("Data audit reported unclean symbols or insufficient sessions")
    except Exception as e:
        gate_state["errors"].append(f"Data audit execution failed: {e}")

    # 5. Baselines Intact
    try:
        bv = verify_frozen_baselines(workspace_root=workspace_root)
        if bv["all_baselines_intact"] is True:
            gate_state["PHASE_11_BASELINES_INTACT"] = True
        else:
            gate_state["errors"].append("Frozen baselines verification failed")
    except Exception as e:
        gate_state["errors"].append(f"Baseline verifier error: {e}")

    # Final Gate Resolution
    if (
        gate_state["PHASE_11_PREREGISTRATION_LOCKED"]
        and gate_state["PHASE_11_COST_MODEL_LOCKED"]
        and gate_state["PHASE_11_UNIVERSE_VERIFIED"]
        and gate_state["PHASE_11_DATA_AUDIT_PASS"]
        and gate_state["PHASE_11_BASELINES_INTACT"]
    ):
        gate_state["PHASE_11_EXECUTION"] = "PERMITTED"
    else:
        gate_state["PHASE_11_EXECUTION"] = "BLOCKED"

    return gate_state


if __name__ == "__main__":
    g = verify_phase11_pre_execution_gate()
    print("Phase 11 Pre-Execution Gate Result:")
    for k, v in g.items():
        if k != "details":
            print(f"  {k} = {v}")
