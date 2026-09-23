"""
Reproducible Backtest Trade Journal Logger.

Stores detailed point-in-time trade logs for ML validation and audit.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from src.backtesting.models import ExecutedTrade, BacktestResult


class TradeJournalLogger:
    """
    Logs executed trades to disk for historical audit and machine learning feature extraction.
    """

    def __init__(self, output_dir: str = "data/trade_journals"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_journal(self, result: BacktestResult, filename: str = "backtest_journal.json") -> str:
        filepath = self.output_dir / filename
        data = {
            "config": result.config.model_dump(mode="json"),
            "data_source": result.data_source,
            "data_quality_label": result.data_quality_label,
            "critical_labels": result.critical_labels,
            "metrics": result.metrics.model_dump(mode="json"),
            "trades": [t.model_dump(mode="json") for t in result.trades],
            "execution_time_sec": result.execution_time_sec,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        return str(filepath)
