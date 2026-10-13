"""
Streamlit Cloud Entrypoint for Indian Stock Market AI.

Serves the standalone modern institutional React trading terminal by default
using Streamlit's native Custom Component runtime, while preserving complete
access to the classic Python Streamlit dashboard via ?view=classic or sidebar toggle.
"""

from __future__ import annotations

import sys
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

# Ensure root directory is in sys.path
_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

dist_path = _root / "frontend" / "dist"

def run_standalone_ui():
    """Render the built React/Next-gen institutional trading terminal."""
    st.set_page_config(
        page_title="Indian Stock Market AI — Flagship Quantitative Terminal",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Fullscreen layout CSS removing Streamlit container margins
    st.markdown(
        """
        <style>
        #MainMenu, header, footer { display: none !important; }
        .block-container {
            padding: 0 !important;
            margin: 0 !important;
            max-width: 100% !important;
        }
        div[data-testid="stVerticalBlock"] {
            gap: 0 !important;
        }
        iframe {
            border: none !important;
            width: 100% !important;
            min-height: 100vh !important;
            display: block !important;
        }
        body {
            background-color: #080B12 !important;
            margin: 0 !important;
            overflow-x: hidden !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Optional classic mode switcher in collapsed sidebar
    with st.sidebar:
        st.markdown("### 🎛️ Terminal Engine")
        st.caption("Active: Standalone React Institutional Terminal (Vite/TS/Tailwind)")
        if st.button("Switch to Classic Streamlit Dashboard", use_container_width=True):
            st.query_params["view"] = "classic"
            st.rerun()

    # Serve the standalone React app directory via Tornado static server
    terminal_component = components.declare_component("flagship_trading_terminal", path=str(dist_path))
    terminal_component()

def main():
    query_view = st.query_params.get("view", "pro")
    if query_view == "classic" or not (dist_path / "index.html").exists():
        from dashboard.app import main as run_classic_app
        run_classic_app()
    else:
        run_standalone_ui()

if __name__ == "__main__":
    main()

