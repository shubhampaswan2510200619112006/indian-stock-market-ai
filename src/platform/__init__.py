"""
Unified Production-Quality Financial Market Research Platform.

Enforces:
- Data-readiness-aware research execution
- Strict separation of data availability, research readiness, and execution readiness
- Plug-and-play provider architecture for future legitimate data
- Permanent preservation of frozen research baselines
- Absolute platform safety invariants
"""

__version__ = "1.0.0"

# Platform Safety Invariants
ALLOW_LIVE_EXECUTION: bool = False
LIVE_EXECUTION: str = "DISABLED"
BROKER: str = "NONE"
AUTO_PAPER_ORDER_SUBMISSION: str = "DISABLED"
OPTIONS_EXECUTION: str = "BLOCKED"
NO_ALPHA_RESEARCH: bool = True  # Safety default; research requires preregistration
NEW_ALPHA_DISCOVERY: str = "DISABLED"
PLATFORM_ENGINEERING: str = "ENABLED"
