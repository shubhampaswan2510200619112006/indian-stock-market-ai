"""
Phase 8 — Paper Session State Manager.

Persistent paper sessions with START/PAUSE/RESUME/STOP lifecycle.
Sessions survive application restart via SQLite persistence.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from src.paper_trading.models import PaperSessionStatus, _generate_id


class PaperSessionManager:
    """
    Manages persistent paper trading sessions.

    Session state survives application restart.
    On crash recovery: load → reconcile → resume/pause safely.
    """

    def __init__(self, state_dir: str = "data/paper_state"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.session_id: Optional[str] = None
        self.started_at: Optional[datetime] = None
        self.stopped_at: Optional[datetime] = None
        self.starting_capital: float = 1_000_000.0
        self.execution_mode: str = "PAPER"
        self.status: PaperSessionStatus = PaperSessionStatus.STOPPED
        self.provider_configuration: Dict[str, Any] = {}
        self.risk_configuration: Dict[str, Any] = {}
        self.model_versions: Dict[str, str] = {}

        # Attempt to load existing session
        self._load_state()

    def start(self, starting_capital: float = 1_000_000.0) -> str:
        """Start a new paper trading session."""
        self.session_id = _generate_id("SES-")
        self.started_at = datetime.now(timezone.utc)
        self.stopped_at = None
        self.starting_capital = starting_capital
        self.status = PaperSessionStatus.STARTED
        self._save_state()
        return self.session_id

    def pause(self) -> None:
        """Pause the current session."""
        if self.status in (PaperSessionStatus.STARTED, PaperSessionStatus.RESUMED):
            self.status = PaperSessionStatus.PAUSED
            self._save_state()

    def resume(self) -> None:
        """Resume a paused session."""
        if self.status == PaperSessionStatus.PAUSED:
            self.status = PaperSessionStatus.RESUMED
            self._save_state()

    def stop(self) -> None:
        """Stop the current session."""
        self.stopped_at = datetime.now(timezone.utc)
        self.status = PaperSessionStatus.STOPPED
        self._save_state()

    @property
    def is_active(self) -> bool:
        return self.status in (PaperSessionStatus.STARTED, PaperSessionStatus.RESUMED)

    def get_session_info(self) -> Dict[str, Any]:
        """Return current session information."""
        return {
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "starting_capital": self.starting_capital,
            "execution_mode": self.execution_mode,
            "status": self.status.value,
        }

    def _save_state(self) -> None:
        """Persist session state to disk."""
        state = {
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "starting_capital": self.starting_capital,
            "execution_mode": self.execution_mode,
            "status": self.status.value,
            "provider_configuration": self.provider_configuration,
            "risk_configuration": self.risk_configuration,
            "model_versions": self.model_versions,
        }
        filepath = self.state_dir / "session_state.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, default=str)

    def _load_state(self) -> None:
        """Load session state from disk (crash recovery)."""
        filepath = self.state_dir / "session_state.json"
        if not filepath.exists():
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                state = json.load(f)

            self.session_id = state.get("session_id")
            if state.get("started_at"):
                self.started_at = datetime.fromisoformat(state["started_at"])
            if state.get("stopped_at"):
                self.stopped_at = datetime.fromisoformat(state["stopped_at"])
            self.starting_capital = state.get("starting_capital", 1_000_000.0)
            self.execution_mode = state.get("execution_mode", "PAPER")

            status_str = state.get("status", "STOPPED")
            self.status = PaperSessionStatus(status_str)

            self.provider_configuration = state.get("provider_configuration", {})
            self.risk_configuration = state.get("risk_configuration", {})
            self.model_versions = state.get("model_versions", {})

            # If session was active at crash, pause it for safe recovery
            if self.status in (PaperSessionStatus.STARTED, PaperSessionStatus.RESUMED):
                self.status = PaperSessionStatus.PAUSED

        except (json.JSONDecodeError, KeyError, ValueError):
            # Corrupted state file — start fresh
            pass

    def reset(self) -> None:
        """Reset session state entirely."""
        self.session_id = None
        self.started_at = None
        self.stopped_at = None
        self.status = PaperSessionStatus.STOPPED
        self._save_state()
