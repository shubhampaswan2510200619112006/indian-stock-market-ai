"""
REST API endpoints for Options Backtesting & Validation.

Endpoints:
- POST /api/v1/backtest/run (non-blocking trigger)
- GET /api/v1/backtest/status/{task_id}
- GET /api/v1/backtest/results/{task_id}
- GET /api/v1/backtest/data-availability/{symbol}
"""

from __future__ import annotations

import uuid
from typing import Dict, Optional
from datetime import date
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from src.backtesting.models import BacktestConfig, BacktestResult
from src.backtesting.engine import BacktestEngine
from src.backtesting.data_gate import DataGate, DataAvailabilityReport

router = APIRouter(prefix="/backtest", tags=["Backtesting & Validation"])

# In-memory task store for backtest background tasks
_BACKTEST_TASKS: Dict[str, Dict] = {}


def _run_backtest_task(task_id: str, config: BacktestConfig):
    _BACKTEST_TASKS[task_id]["status"] = "RUNNING"
    try:
        engine = BacktestEngine(config)
        result = engine.run()
        _BACKTEST_TASKS[task_id]["status"] = "COMPLETED"
        _BACKTEST_TASKS[task_id]["result"] = result
    except Exception as e:
        _BACKTEST_TASKS[task_id]["status"] = "FAILED"
        _BACKTEST_TASKS[task_id]["error"] = str(e)


@router.get("/data-availability/{symbol}", response_model=DataAvailabilityReport)
def check_data_availability(
    symbol: str,
    start_date: str = Query("2026-01-01"),
    end_date: str = Query("2026-02-01"),
):
    """
    Evaluates whether genuine historical options quotes exist for a given symbol and date range.
    """
    try:
        s_date = date.fromisoformat(start_date)
        e_date = date.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    gate = DataGate()
    return gate.evaluate_availability(symbol=symbol, start_date=s_date, end_date=e_date)


@router.post("/run")
def start_backtest(
    config: BacktestConfig,
    background_tasks: BackgroundTasks,
):
    """
    Triggers a non-blocking options strategy backtest simulation.
    """
    task_id = str(uuid.uuid4())[:8]
    _BACKTEST_TASKS[task_id] = {
        "task_id": task_id,
        "status": "PENDING",
        "config": config,
        "result": None,
        "error": None,
    }

    background_tasks.add_task(_run_backtest_task, task_id, config)

    return {
        "task_id": task_id,
        "status": "PENDING",
        "message": f"Backtest launched for {config.symbol} ({config.strategy_name}). Poll status at /api/v1/backtest/status/{task_id}",
    }


@router.get("/status/{task_id}")
def get_backtest_status(task_id: str):
    """
    Gets the current status of a running or completed backtest task.
    """
    task = _BACKTEST_TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")

    return {
        "task_id": task_id,
        "status": task["status"],
        "error": task["error"],
    }


@router.get("/results/{task_id}", response_model=BacktestResult)
def get_backtest_results(task_id: str):
    """
    Fetches the completed BacktestResult for a given task ID.
    """
    task = _BACKTEST_TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")

    if task["status"] == "RUNNING" or task["status"] == "PENDING":
        raise HTTPException(status_code=202, detail="Backtest is still running. Please poll later.")

    if task["status"] == "FAILED":
        raise HTTPException(status_code=500, detail=f"Backtest failed: {task['error']}")

    return task["result"]


@router.get("/data-audit/{symbol}")
def audit_historical_data(
    symbol: str,
    start_date: str = Query("2026-01-01"),
    end_date: str = Query("2026-02-01"),
):
    """
    Audits dataset completeness, missing fields, expiries, strikes, and timestamp gaps.
    """
    try:
        s_date = date.fromisoformat(start_date)
        e_date = date.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    from src.ingestion.historical_provider import DatabaseHistoricalOptionsProvider
    provider = DatabaseHistoricalOptionsProvider()
    return provider.audit_dataset_quality(symbol=symbol, start_date=s_date, end_date=e_date)


@router.get("/ml-gate-status")
def get_ml_gate_status(symbol: str = Query("NIFTY")):
    """
    Evaluates ML Readiness Gate checklist before allowing Phase 6 ML development.
    """
    from src.backtesting.ml_gate import MLGateEvaluator
    evaluator = MLGateEvaluator()
    return evaluator.evaluate_gate(symbol=symbol)
