"""
Automatic Readiness and Execution Gates.
"""

from src.platform.gates.readiness_gate import ReadinessGate, GateResult
from src.platform.gates.execution_gate import ExecutionGate, ExecutionGateResult

__all__ = [
    "ReadinessGate",
    "GateResult",
    "ExecutionGate",
    "ExecutionGateResult",
]
