"""
Execution Timing Integrity & Audit Tracker (Phase 6.5).
Enforces Model A (Next-Session Execution) and tracks execution provenance and refusal reasons.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple


class ExecutionPriceSource(str, Enum):
    NSE_HISTORICAL_OPTION_QUOTE = "NSE_HISTORICAL_OPTION_QUOTE"
    NSE_HISTORICAL_OPEN = "NSE_HISTORICAL_OPEN"
    BROKER_HISTORICAL_TICK = "BROKER_HISTORICAL_TICK"
    EOD_UNSUITABLE_PROXY = "EOD_UNSUITABLE_PROXY"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass
class ExecutionTimestampRecord:
    feature_availability_timestamp: datetime  # e.g., T 15:30:00
    prediction_timestamp: datetime            # e.g., T 15:31:00
    order_timestamp: datetime                 # e.g., T+1 09:15:00
    execution_timestamp: Optional[datetime]    # Genuine observation timestamp
    execution_price: Optional[float]
    execution_price_source: ExecutionPriceSource
    is_executed: bool
    refusal_reason: Optional[str] = None


@dataclass
class ExecutionAuditReport:
    attempted_executions: int = 0
    successful_executions: int = 0
    refused_executions: int = 0
    refusal_reasons: Dict[str, int] = field(default_factory=dict)
    execution_timestamp_distribution: List[str] = field(default_factory=list)
    execution_price_source_distribution: Dict[str, int] = field(default_factory=dict)
    timestamp_records: List[ExecutionTimestampRecord] = field(default_factory=list)

    def record_attempt(
        self,
        t_feat: datetime,
        t_pred: datetime,
        t_order: datetime,
        t_exec: Optional[datetime],
        price: Optional[float],
        source: ExecutionPriceSource,
        is_executed: bool,
        refusal_reason: Optional[str] = None,
    ) -> ExecutionTimestampRecord:
        self.attempted_executions += 1
        src_name = source.value

        if is_executed and price is not None:
            self.successful_executions += 1
            self.execution_price_source_distribution[src_name] = self.execution_price_source_distribution.get(src_name, 0) + 1
            if t_exec:
                self.execution_timestamp_distribution.append(t_exec.isoformat())
        else:
            self.refused_executions += 1
            reason = refusal_reason or "GENUINE_NEXT_SESSION_DATA_UNAVAILABLE"
            self.refusal_reasons[reason] = self.refusal_reasons.get(reason, 0) + 1

        rec = ExecutionTimestampRecord(
            feature_availability_timestamp=t_feat,
            prediction_timestamp=t_pred,
            order_timestamp=t_order,
            execution_timestamp=t_exec,
            execution_price=price if is_executed else None,
            execution_price_source=source if is_executed else ExecutionPriceSource.UNAVAILABLE,
            is_executed=is_executed,
            refusal_reason=refusal_reason,
        )
        self.timestamp_records.append(rec)
        return rec


class ModelAExecutionTimer:
    """
    Model A Execution Timing Auditor.
    Computes strict non-overlapping timestamps for Model A:
    T 15:30 -> T 15:31 -> T+1 09:15 -> T+1 09:15:30+
    """

    @staticmethod
    def derive_model_a_timestamps(observation_date: datetime) -> Tuple[datetime, datetime, datetime]:
        """
        Given EOD observation date T:
        Returns (feature_availability_timestamp, prediction_timestamp, order_timestamp)
        """
        # Feature availability at 15:30:00 on date T
        t_feat = datetime(observation_date.year, observation_date.month, observation_date.day, 15, 30, 0)
        # Prediction generated at 15:31:00 on date T
        t_pred = datetime(observation_date.year, observation_date.month, observation_date.day, 15, 31, 0)

        # Order becomes eligible at next session open 09:15:00 on date T+1
        # Skip weekend if Friday
        next_day = observation_date + timedelta(days=1)
        if next_day.weekday() == 5:  # Saturday
            next_day += timedelta(days=2)
        elif next_day.weekday() == 6:  # Sunday
            next_day += timedelta(days=1)

        t_order = datetime(next_day.year, next_day.month, next_day.day, 9, 15, 0)
        return t_feat, t_pred, t_order
