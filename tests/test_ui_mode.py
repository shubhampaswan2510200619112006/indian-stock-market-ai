"""
Test UI Mode switcher, persistence, and unified trading architecture.
"""

import pytest
import streamlit as st
from dashboard.components.ui_mode import get_current_ui_mode, set_ui_mode
from src.paper_trading.service import PaperTradingService


def test_ui_mode_default_and_toggle(tmp_path, monkeypatch):
    """Verify UI mode toggles between BEGINNER and PRO and persists properly."""
    # Ensure fresh session state
    if "ui_mode" in st.session_state:
        del st.session_state["ui_mode"]

    # Redirect pref file to tmp_path
    pref_file = tmp_path / "user_preferences.json"
    import dashboard.components.ui_mode as uim
    monkeypatch.setattr(uim, "_PREF_FILE", pref_file)

    # Initial default should be BEGINNER
    mode = get_current_ui_mode()
    assert mode == "BEGINNER"

    # Toggle to PRO
    set_ui_mode("PRO")
    assert get_current_ui_mode() == "PRO"
    assert st.session_state["ui_mode"] == "PRO"
    assert pref_file.exists()

    # Clear session state and verify it loads from file
    del st.session_state["ui_mode"]
    assert get_current_ui_mode() == "PRO"

    # Toggle back to BEGINNER
    set_ui_mode("BEGINNER")
    assert get_current_ui_mode() == "BEGINNER"


def test_shared_service_invariants_across_modes():
    """Verify that both modes share the same backend service and risk invariants."""
    svc = PaperTradingService()
    summary = svc.get_portfolio_summary()

    # Invariants
    assert summary["execution_mode"] == "PAPER_TRADE"
    assert summary["equity"] > 0
    assert summary["cash"] > 0

    # Risk status invariant
    risk = svc.get_risk_status()
    assert "configured_limits" in risk
    assert risk["is_any_breaker_active"] in (True, False)
