"""
Out-of-Distribution (OOD) Drift Monitoring Engine (Phase 7).
Monitors live-vs-training feature drift and preserves Phase 6.5 research status disclaimers.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import numpy as np


class OODStatus(str, Enum):
    NORMAL = "NORMAL"
    DRIFT_WARNING = "DRIFT_WARNING"
    OOD = "OOD"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass
class OODEvaluationRecord:
    timestamp: str
    feature_name: str
    training_mean: float
    training_std: float
    live_mean: float
    live_std: float
    comparison_method: str
    z_score: float
    status: OODStatus


class OODDetector:
    """
    Monitors live feature distributions against Phase 6 training baseline distributions.
    Flags OOD or DRIFT_WARNING when live market volatility or returns diverge materially.
    """

    # PHASE 17 AUDIT NOTE:
    # These baselines are HARD-CODED APPROXIMATIONS based on general NIFTY market knowledge.
    # They are NOT fitted from a held-out training set.
    # Until a real ML model is trained and baselines are extracted from it, OOD detection
    # provides directional guidance only, not a statistically rigorous drift test.
    # Status: HEURISTIC_BASELINE — not from fitted model
    TRAINING_BASELINES = {
        "ret_1d": {"mean": 0.0012, "std": 0.0085},
        "rv_5d": {"mean": 0.1350, "std": 0.0250},
        "high_low_ratio": {"mean": 0.0095, "std": 0.0030},
    }
    BASELINES_SOURCE = "HARD_CODED_APPROXIMATION"  # Will become FITTED_FROM_TRAINING when real model exists

    def evaluate_live_features(self, live_feature_dict: Dict[str, float]) -> Dict[str, Any]:
        """
        Evaluates live features against training distributions.
        Returns aggregate OOD status and feature-level records.
        """
        now_str = datetime.now(timezone.utc).isoformat()
        records: List[OODEvaluationRecord] = []
        max_z = 0.0

        for feat, val in live_feature_dict.items():
            if feat in self.TRAINING_BASELINES:
                tr_m = self.TRAINING_BASELINES[feat]["mean"]
                tr_s = self.TRAINING_BASELINES[feat]["std"]
                z = abs(val - tr_m) / (tr_s + 1e-6)
                max_z = max(max_z, z)

                if z > 3.0:
                    st = OODStatus.OOD
                elif z > 2.0:
                    st = OODStatus.DRIFT_WARNING
                else:
                    st = OODStatus.NORMAL

                records.append(
                    OODEvaluationRecord(
                        timestamp=now_str,
                        feature_name=feat,
                        training_mean=tr_m,
                        training_std=tr_s,
                        live_mean=float(val),
                        live_std=tr_s,
                        comparison_method="Z-Score Thresholding",
                        z_score=round(z, 2),
                        status=st,
                    )
                )

        if max_z > 3.0:
            agg_status = OODStatus.OOD.value
        elif max_z > 2.0:
            agg_status = OODStatus.DRIFT_WARNING.value
        else:
            agg_status = OODStatus.NORMAL.value

        return {
            "overall_status": agg_status,
            "max_z_score": round(max_z, 2),
            "research_banner": "MODEL RESEARCH STATUS: LIMITED DATA / INSUFFICIENT STATISTICAL EVIDENCE",
            "evaluations": [r.__dict__ for r in records],
        }

    def detect(self, live_feature_dict: Dict[str, float]) -> Dict[str, Any]:
        """
        Dashboard and API compatible wrapper around evaluate_live_features.
        Returns status enum, max_z_score, flagged_features, and recommendation.
        """
        eval_res = self.evaluate_live_features(live_feature_dict)
        raw_status = eval_res.get("overall_status", "NORMAL")
        status_enum = OODStatus(raw_status) if raw_status in [s.value for s in OODStatus] else OODStatus.NORMAL
        flagged = [
            e["feature_name"]
            for e in eval_res.get("evaluations", [])
            if e.get("z_score", 0) > 2.0
        ]
        if status_enum == OODStatus.NORMAL:
            rec = "Features within baseline distribution. Predictions within expected variance."
        elif status_enum == OODStatus.DRIFT_WARNING:
            rec = "Feature drift detected — volatility/returns moving away from baseline. Exercise caution."
        else:
            rec = "OUT-OF-DISTRIBUTION: Significant regime divergence. AI models should NOT be trusted blindly."

        return {
            "status": status_enum,
            "overall_status": raw_status,
            "max_z_score": eval_res.get("max_z_score", 0.0),
            "recommendation": rec,
            "flagged_features": flagged,
            "research_banner": eval_res.get("research_banner", ""),
            "evaluations": eval_res.get("evaluations", []),
        }

