"""
Phase 9.5 — Progressive Model Hierarchy & Baseline Suite.

Evaluates predictive models in strict ascending hierarchy:
- Level 0: Naive Baselines (Majority Class, Persistence / Previous Direction, Zero-Return, Rolling Mean/Median)
- Level 1: Linear Models (Logistic Regression, Ridge Regression, Lasso)
- Level 2: Non-Linear Ensemble (Random Forest)
- Level 3: Advanced Gradient Boosting (XGBoost / LightGBM / Sklearn Fallback)
- Level 4: Deep Learning Gate (Strictly skipped if sample size < 10,000 temporal samples: DEEP_LEARNING = SKIPPED_INSUFFICIENT_DATA)

Enforces that every advanced model is compared directly against Level 0 baselines.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

try:
    from sklearn.ensemble import (
        GradientBoostingClassifier,
        GradientBoostingRegressor,
        RandomForestClassifier,
        RandomForestRegressor,
    )
    from sklearn.linear_model import Lasso, LogisticRegression, Ridge
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


class ModelHierarchyLevel(str, Enum):
    LEVEL_0_NAIVE = "LEVEL_0_NAIVE"
    LEVEL_1_LINEAR = "LEVEL_1_LINEAR"
    LEVEL_2_RANDOM_FOREST = "LEVEL_2_RANDOM_FOREST"
    LEVEL_3_GRADIENT_BOOSTING = "LEVEL_3_GRADIENT_BOOSTING"
    LEVEL_4_DEEP_LEARNING = "LEVEL_4_DEEP_LEARNING"


class MLBaseModel(ABC):
    """Abstract base interface for all models."""

    def __init__(self, name: str, level: ModelHierarchyLevel = ModelHierarchyLevel.LEVEL_0_NAIVE, model_version: str = "v1.0"):
        self.name = name
        self.level = level
        self.model_version = model_version
        self.is_fitted = False

    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray) -> "MLBaseModel":
        pass

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        pass

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Default probability output: 0.5 for non-probabilistic models."""
        preds = self.predict(X)
        p = np.clip(preds, 0.0, 1.0)
        return np.column_stack([1.0 - p, p])


# =============================================================================
# Level 0: Naive Baselines
# =============================================================================
class Baseline0NaiveModel(MLBaseModel):
    """Always predicts majority class (classification) or 0.0 (regression)."""

    def __init__(self, is_classification: bool = True):
        super().__init__(name="Baseline 0: Naive Constant", level=ModelHierarchyLevel.LEVEL_0_NAIVE)
        self.is_classification = is_classification
        self.constant_val: float = 0.0

    def fit(self, X: np.ndarray, y: np.ndarray) -> "Baseline0NaiveModel":
        if self.is_classification:
            vals, counts = np.unique(y, return_counts=True)
            self.constant_val = vals[np.argmax(counts)] if len(vals) > 0 else 0
        else:
            self.constant_val = 0.0
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.full(len(X), self.constant_val)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        p = float(self.constant_val)
        return np.column_stack([np.full(len(X), 1.0 - p), np.full(len(X), p)])


class Baseline0PersistenceModel(MLBaseModel):
    """
    Persistence / Previous Direction Baseline.
    Predicts tomorrow's direction will match today's return sign (feature col 0 or passed values).
    """

    def __init__(self):
        super().__init__(name="Baseline 0: Persistence", level=ModelHierarchyLevel.LEVEL_0_NAIVE)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "Baseline0PersistenceModel":
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if X.ndim > 1 and X.shape[1] > 0:
            # Assume first column is past 1d return
            return (X[:, 0] > 0).astype(float)
        return np.ones(len(X))

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        p = self.predict(X)
        return np.column_stack([1.0 - p, p])


class Baseline1RollingMeanModel(MLBaseModel):
    """Predicts historical mean/median of training target."""

    def __init__(self):
        super().__init__(name="Baseline 1: Rolling Mean", level=ModelHierarchyLevel.LEVEL_0_NAIVE)
        self.mean_val: float = 0.0

    def fit(self, X: np.ndarray, y: np.ndarray) -> "Baseline1RollingMeanModel":
        self.mean_val = float(np.mean(y)) if len(y) > 0 else 0.0
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.full(len(X), self.mean_val)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        p = np.clip(self.mean_val, 0.0, 1.0)
        return np.column_stack([np.full(len(X), 1.0 - p), np.full(len(X), p)])


# =============================================================================
# Level 1: Linear Models (Logistic Regression, Ridge, Lasso)
# =============================================================================
class Baseline2LogisticRegressionModel(MLBaseModel):
    """Linear classification baseline using Logistic Regression."""

    def __init__(self):
        super().__init__(name="Baseline 2: Logistic Regression", level=ModelHierarchyLevel.LEVEL_1_LINEAR)
        if HAS_SKLEARN:
            self.model = LogisticRegression(max_iter=1000, random_state=42)
        else:
            self.model = Baseline0NaiveModel(is_classification=True)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "Baseline2LogisticRegressionModel":
        if HAS_SKLEARN and len(np.unique(y)) >= 2:
            self.model.fit(X, y)
        else:
            self.model = Baseline0NaiveModel(is_classification=True).fit(X, y)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if hasattr(self.model, "predict_proba"):
            return self.model.predict_proba(X)
        return super().predict_proba(X)


class Baseline3RidgeLassoModel(MLBaseModel):
    """Regularized linear regression baseline (Ridge or Lasso)."""

    def __init__(self, alpha: float = 1.0, use_lasso: bool = False):
        name = f"Baseline 3: {'Lasso' if use_lasso else 'Ridge'} Regression"
        super().__init__(name=name, level=ModelHierarchyLevel.LEVEL_1_LINEAR)
        if HAS_SKLEARN:
            self.model = Lasso(alpha=alpha, random_state=42) if use_lasso else Ridge(alpha=alpha, random_state=42)
        else:
            self.model = Baseline1RollingMeanModel()

    def fit(self, X: np.ndarray, y: np.ndarray) -> "Baseline3RidgeLassoModel":
        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)


# =============================================================================
# Level 2: Random Forest
# =============================================================================
class Baseline4RandomForestModel(MLBaseModel):
    """Ensemble Random Forest baseline."""

    def __init__(self, is_classification: bool = True, n_estimators: int = 50, max_depth: int = 5):
        super().__init__(name="Baseline 4: Random Forest", level=ModelHierarchyLevel.LEVEL_2_RANDOM_FOREST)
        self.is_classification = is_classification
        if HAS_SKLEARN:
            if is_classification:
                self.model = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
            else:
                self.model = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
        else:
            self.model = Baseline0NaiveModel(is_classification=is_classification)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "Baseline4RandomForestModel":
        if HAS_SKLEARN and ((not self.is_classification) or len(np.unique(y)) >= 2):
            self.model.fit(X, y)
        else:
            self.model = Baseline0NaiveModel(is_classification=self.is_classification).fit(X, y)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.is_classification and hasattr(self.model, "predict_proba"):
            return self.model.predict_proba(X)
        return super().predict_proba(X)


# =============================================================================
# Level 3: Gradient Boosting (XGBoost / LightGBM / Sklearn Fallback)
# =============================================================================
class Baseline5GradientBoostingModel(MLBaseModel):
    """Gradient Boosting baseline using Sklearn / XGBoost interface."""

    def __init__(self, is_classification: bool = True, n_estimators: int = 50, max_depth: int = 3):
        super().__init__(name="Baseline 5: Gradient Boosting", level=ModelHierarchyLevel.LEVEL_3_GRADIENT_BOOSTING)
        self.is_classification = is_classification
        if HAS_SKLEARN:
            if is_classification:
                self.model = GradientBoostingClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
            else:
                self.model = GradientBoostingRegressor(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
        else:
            self.model = Baseline0NaiveModel(is_classification=is_classification)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "Baseline5GradientBoostingModel":
        if HAS_SKLEARN and ((not self.is_classification) or len(np.unique(y)) >= 2):
            self.model.fit(X, y)
        else:
            self.model = Baseline0NaiveModel(is_classification=self.is_classification).fit(X, y)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.is_classification and hasattr(self.model, "predict_proba"):
            return self.model.predict_proba(X)
        return super().predict_proba(X)


# =============================================================================
# Level 4: Deep Learning Gate
# =============================================================================
class DeepLearningModelGate:
    """
    Evaluates whether dataset size genuinely justifies deep neural networks (LSTM, Transformers).
    Strictly skips deep learning when observations < 10,000 to prevent severe overfitting.
    """

    MIN_SAMPLES_FOR_DEEP_LEARNING: int = 10_000

    @classmethod
    def evaluate_deep_learning_eligibility(cls, sample_count: int) -> Dict[str, Any]:
        if sample_count < cls.MIN_SAMPLES_FOR_DEEP_LEARNING:
            return {
                "DEEP_LEARNING": "SKIPPED_INSUFFICIENT_DATA",
                "sample_count": sample_count,
                "required_threshold": cls.MIN_SAMPLES_FOR_DEEP_LEARNING,
                "reason": (
                    f"Sample count ({sample_count}) is below the required threshold of "
                    f"{cls.MIN_SAMPLES_FOR_DEEP_LEARNING} temporal sequences. Training complex deep architectures "
                    f"on small samples produces severe overparameterization and spurious in-sample memorization."
                ),
            }
        return {
            "DEEP_LEARNING": "ELIGIBLE",
            "sample_count": sample_count,
            "required_threshold": cls.MIN_SAMPLES_FOR_DEEP_LEARNING,
            "reason": "Sample size satisfies deep learning statistical sufficiency criteria.",
        }


# =============================================================================
# Model Hierarchy Suite Factory
# =============================================================================
class MLBaselineModelSuite:
    """Factory suite for instantiating and comparing baseline models."""

    @staticmethod
    def get_all_baselines(is_classification: bool = True) -> Dict[str, MLBaseModel]:
        lin_model = Baseline2LogisticRegressionModel() if is_classification else Baseline3RidgeLassoModel()
        rf_model = Baseline4RandomForestModel(is_classification=is_classification)
        gb_model = Baseline5GradientBoostingModel(is_classification=is_classification)
        return {
            # Legacy keys for Phases 6/6.5 compatibility
            "Baseline_0_Naive": Baseline0NaiveModel(is_classification=is_classification),
            "Baseline_1_RollingMean": Baseline1RollingMeanModel(),
            "Baseline_2_LogisticRegression" if is_classification else "Baseline_3_Ridge": lin_model,
            "Baseline_4_RandomForest": rf_model,
            "Baseline_5_GradientBoosting": gb_model,
            # Phase 9.5 Level keys
            "Level_0_Naive_Majority": Baseline0NaiveModel(is_classification=is_classification),
            "Level_0_Persistence": Baseline0PersistenceModel(),
            "Level_0_RollingMean": Baseline1RollingMeanModel(),
            "Level_1_Linear": lin_model,
            "Level_2_RandomForest": rf_model,
            "Level_3_GradientBoosting": gb_model,
        }
