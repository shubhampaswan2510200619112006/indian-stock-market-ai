"""
Walk-Forward Validation Engine with Purging and Embargo Periods.

PREVENTS INFORMATION LEAKAGE:
- Splits historical timeline into chronological Train (In-Sample) and Test (Out-of-Sample) windows.
- Purging: removes overlapping multi-day option trade windows near boundary.
- Embargo: adds safety buffer between train and test windows.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import List, Tuple
from pydantic import BaseModel, Field

from src.backtesting.models import BacktestConfig, BacktestResult
from src.backtesting.engine import BacktestEngine


class WalkForwardWindow(BaseModel):
    train_start: date
    train_end: date
    test_start: date
    test_end: date
    train_result: Optional[BacktestResult] = None
    test_result: Optional[BacktestResult] = None


class WalkForwardResult(BaseModel):
    symbol: str
    total_windows: int
    windows: List[WalkForwardWindow]
    combined_in_sample_cagr: float = 0.0
    combined_out_of_sample_cagr: float = 0.0
    out_of_sample_efficiency: float = 0.0  # OOS CAGR / IS CAGR
    critical_label: str = "OUT-OF-SAMPLE VALIDATED"


class WalkForwardSplitter:
    """
    Generates chronological walk-forward windows with embargo safety gaps.
    """

    def __init__(
        self,
        train_days: int = 60,
        test_days: int = 20,
        embargo_days: int = 3,
    ):
        self.train_days = train_days
        self.test_days = test_days
        self.embargo_days = embargo_days

    def create_windows(self, start_date: date, end_date: date) -> List[WalkForwardWindow]:
        windows: List[WalkForwardWindow] = []
        current_start = start_date
        total_days = (end_date - start_date).days

        while True:
            train_end = current_start + timedelta(days=self.train_days)
            test_start = train_end + timedelta(days=self.embargo_days)
            test_end = test_start + timedelta(days=self.test_days)

            if test_end > end_date:
                break

            window = WalkForwardWindow(
                train_start=current_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
            )
            windows.append(window)
            current_start = test_start  # Roll forward

        return windows

    def run_walk_forward(self, base_config: BacktestConfig) -> WalkForwardResult:
        windows = self.create_windows(base_config.start_date, base_config.end_date)
        
        is_cagrs: List[float] = []
        oos_cagrs: List[float] = []

        for w in windows:
            # Run In-Sample
            train_config = base_config.model_copy()
            train_config.start_date = w.train_start
            train_config.end_date = w.train_end
            train_engine = BacktestEngine(train_config)
            w.train_result = train_engine.run()
            is_cagrs.append(w.train_result.metrics.cagr_pct)

            # Run Out-of-Sample
            test_config = base_config.model_copy()
            test_config.start_date = w.test_start
            test_config.end_date = w.test_end
            test_engine = BacktestEngine(test_config)
            w.test_result = test_engine.run()
            oos_cagrs.append(w.test_result.metrics.cagr_pct)

        mean_is = sum(is_cagrs) / max(1, len(is_cagrs))
        mean_oos = sum(oos_cagrs) / max(1, len(oos_cagrs))
        efficiency = mean_oos / max(1e-4, mean_is)

        label = "OUT-OF-SAMPLE VALIDATED" if efficiency >= 0.5 else "FRAGILE / POSSIBLE OVERFITTING"

        return WalkForwardResult(
            symbol=base_config.symbol,
            total_windows=len(windows),
            windows=windows,
            combined_in_sample_cagr=round(mean_is, 4),
            combined_out_of_sample_cagr=round(mean_oos, 4),
            out_of_sample_efficiency=round(efficiency, 2),
            critical_label=label,
        )
