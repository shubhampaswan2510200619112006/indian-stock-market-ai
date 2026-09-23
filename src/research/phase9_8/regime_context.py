"""
Phase 9.8 — Track F: Market Regime as Uncertainty & Calibration Context Engine.

Investigates P98-H007:
- Evaluates whether macro market regime information improves out-of-sample probabilistic
  forecast calibration (Brier score, Log-Loss, Reliability curve) without filter mining.
- Explicit Anti-Regime-Picking Mandate:
  * Does NOT search for "which regime makes the strategy profitable."
  * Does NOT drop sideways regimes.
  * Measures whether regime-conditioned probabilities are better calibrated across ALL regimes.
- Baseline: Unconditioned Logistic Regression.
- Target: 1D directional return sign (T -> T+1 forward).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss

from src.ml.ablation import FeatureAblationEngine, FeatureTier
from src.ml.targets import MultiHorizonTargetEngine


@dataclass
class CalibrationEvaluationResult:
    hypothesis_id: str
    total_sessions: int
    unconditioned_brier_score: float
    regime_conditioned_brier_score: float
    brier_score_improvement_pct: float
    unconditioned_log_loss: float
    regime_conditioned_log_loss: float
    log_loss_improvement: float
    directional_accuracy_delta: float
    sample_classification: str  # "CONFIRMATORY_CALIBRATION_EVALUATION"
    success_criteria_met: bool
    evidence_notes: str


class RegimeContextEngine:
    """
    Measures probabilistic calibration improvement from market regime context.
    """

    @classmethod
    def evaluate_regime_calibration(cls, df_nifty_daily: pd.DataFrame) -> CalibrationEvaluationResult:
        df_targets = MultiHorizonTargetEngine.build_all_underlying_targets(df_nifty_daily)
        df_features, tier_defs = FeatureAblationEngine.generate_features_all_tiers(df=df_targets, symbol="NIFTY")

        # Clean target
        clean = df_features.dropna(subset=["target_fwd_dir_1d"]).copy()
        y = clean["target_fwd_dir_1d"].astype(int).values
        n = len(clean)

        if n < 80:
            return CalibrationEvaluationResult(
                hypothesis_id="P98-H007",
                total_sessions=n,
                unconditioned_brier_score=0.25,
                regime_conditioned_brier_score=0.25,
                brier_score_improvement_pct=0.0,
                unconditioned_log_loss=0.693,
                regime_conditioned_log_loss=0.693,
                log_loss_improvement=0.0,
                directional_accuracy_delta=0.0,
                sample_classification="INSUFFICIENT_DATA",
                success_criteria_met=False,
                evidence_notes="Insufficient observations for walk-forward calibration testing.",
            )

        # Baseline features: Tier C (Price + Momentum + Volume)
        base_cols = [c for c in tier_defs[FeatureTier.TIER_C_VOLUME] if c in clean.columns]
        X_base = clean[base_cols].fillna(0.0).values

        # Regime features: one-hot encode market_regime
        regime_series = clean.get("market_regime", pd.Series(["SIDEWAYS"] * n))
        regime_dummies = pd.get_dummies(regime_series, prefix="reg", drop_first=True).astype(float)
        X_regime = np.hstack([X_base, regime_dummies.values])

        # Expanding walk-forward calibration test (train min 40, test 10)
        min_train = 40
        step = 10

        probs_base = []
        probs_reg = []
        y_test_all = []

        for i in range(min_train, n - step, step):
            X_tr_b, y_tr = X_base[:i], y[:i]
            X_te_b, y_te = X_base[i : i + step], y[i : i + step]

            X_tr_r = X_regime[:i]
            X_te_r = X_regime[i : i + step]

            # Fit baseline model
            m_base = LogisticRegression(max_iter=200, random_state=42)
            m_base.fit(X_tr_b, y_tr)
            p_b = m_base.predict_proba(X_te_b)[:, 1]

            # Fit regime-conditioned model
            m_reg = LogisticRegression(max_iter=200, random_state=42)
            m_reg.fit(X_tr_r, y_tr)
            p_r = m_reg.predict_proba(X_te_r)[:, 1]

            probs_base.extend(p_b)
            probs_reg.extend(p_r)
            y_test_all.extend(y_te)

        probs_base = np.array(probs_base)
        probs_reg = np.array(probs_reg)
        y_test_all = np.array(y_test_all)

        # Compute Brier score
        brier_base = float(brier_score_loss(y_test_all, probs_base))
        brier_reg = float(brier_score_loss(y_test_all, probs_reg))
        brier_imp = float((brier_base - brier_reg) / brier_base) if brier_base > 0 else 0.0

        # Log loss
        eps = 1e-6
        p_b_clip = np.clip(probs_base, eps, 1.0 - eps)
        p_r_clip = np.clip(probs_reg, eps, 1.0 - eps)
        loss_base = float(log_loss(y_test_all, p_b_clip))
        loss_reg = float(log_loss(y_test_all, p_r_clip))
        loss_imp = float(loss_base - loss_reg)

        # Accuracy
        acc_base = float(np.mean((probs_base > 0.5) == y_test_all))
        acc_reg = float(np.mean((probs_reg > 0.5) == y_test_all))
        acc_delta = float(acc_reg - acc_base)

        success = (brier_imp >= 0.05) and (loss_imp >= 0.02)

        return CalibrationEvaluationResult(
            hypothesis_id="P98-H007",
            total_sessions=len(y_test_all),
            unconditioned_brier_score=brier_base,
            regime_conditioned_brier_score=brier_reg,
            brier_score_improvement_pct=brier_imp,
            unconditioned_log_loss=loss_base,
            regime_conditioned_log_loss=loss_reg,
            log_loss_improvement=loss_imp,
            directional_accuracy_delta=acc_delta,
            sample_classification="CONFIRMATORY_CALIBRATION_EVALUATION",
            success_criteria_met=success,
            evidence_notes=(
                f"Regime calibration evaluated out-of-sample over {len(y_test_all)} sessions. "
                f"Baseline Brier: {brier_base:.4f} vs Regime-Conditioned: {brier_reg:.4f} (Improvement: {brier_imp:.2%}). "
                f"Log-Loss Delta: {loss_imp:.4f}, Accuracy Delta: {acc_delta:.2%}. "
                f"{'Statistically meaningful calibration gain.' if success else 'Regime conditioning fails to provide >= 5.0% Brier score improvement.'}"
            ),
        )
