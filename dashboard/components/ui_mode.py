"""
UI Mode Manager — Supports Seamless Toggle Between Beginner and Pro Modes.

Persists preferences safely to local storage and st.session_state.
Shares exact same underlying portfolio, risk controls, and execution engine.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal
import streamlit as st

_PREF_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "user_preferences.json"

UIMode = Literal["BEGINNER", "PRO"]


def get_current_ui_mode() -> UIMode:
    """Retrieve the currently active UI mode from session state or persisted file."""
    if "ui_mode" in st.session_state:
        return st.session_state["ui_mode"]

    # Try loading from disk
    try:
        if _PREF_FILE.exists():
            with open(_PREF_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                mode = data.get("ui_mode", "BEGINNER")
                if mode in ("BEGINNER", "PRO"):
                    st.session_state["ui_mode"] = mode
                    return mode
    except Exception:
        pass

    # Default to BEGINNER for inclusive onboarding
    st.session_state["ui_mode"] = "BEGINNER"
    return "BEGINNER"


def set_ui_mode(mode: UIMode) -> None:
    """Set and persist the UI mode."""
    st.session_state["ui_mode"] = mode
    try:
        _PREF_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if _PREF_FILE.exists():
            try:
                with open(_PREF_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data["ui_mode"] = mode
        with open(_PREF_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def render_mode_switcher_sidebar():
    """Render the prominent mode toggle switch in the sidebar."""
    current_mode = get_current_ui_mode()

    st.sidebar.markdown(
        """
        <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8; margin-bottom: 6px; font-weight: 600;">
            PLATFORM EXPERIENCE
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.sidebar.columns([1, 1])
    with col1:
        is_beginner = current_mode == "BEGINNER"
        btn_beg_label = "🔰 Beginner" if is_beginner else "Beginner"
        if st.button(
            btn_beg_label,
            key="btn_switch_beginner",
            use_container_width=True,
            type="primary" if is_beginner else "secondary",
        ):
            if current_mode != "BEGINNER":
                set_ui_mode("BEGINNER")
                st.rerun()

    with col2:
        is_pro = current_mode == "PRO"
        btn_pro_label = "⚡ Pro" if is_pro else "Pro"
        if st.button(
            btn_pro_label,
            key="btn_switch_pro",
            use_container_width=True,
            type="primary" if is_pro else "secondary",
        ):
            if current_mode != "PRO":
                set_ui_mode("PRO")
                st.rerun()

    if current_mode == "BEGINNER":
        st.sidebar.caption("🔰 **Beginner Mode:** Guided workflows, plain English & built-in safety tips.")
    else:
        st.sidebar.caption("⚡ **Pro Mode:** Dense terminal data, Greeks, technicals & institutional tools.")

    st.sidebar.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
