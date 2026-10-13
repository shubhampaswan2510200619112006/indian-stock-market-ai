"""
Indian Stock Market AI — Master Unified Trading Platform.
Directly serves the state-of-the-art React Quantitative Intelligence Terminal
as the flagship, primary user experience.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on the Python path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from typing import Optional
import streamlit as st
import streamlit.components.v1 as components

from src.database.connection import init_db

# Page configuration — must be first Streamlit command
st.set_page_config(
    page_title="Indian Stock Market AI — Trading Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Initialize database schema if not present
try:
    init_db()
except Exception:
    pass

# Locate frontend distribution directory
_dist_dir = _project_root / "frontend" / "dist"
if not _dist_dir.exists():
    _dist_dir = Path("frontend/dist")


def main():
    """Main application orchestrator serving the Flagship Quantitative Terminal."""
    # Inject full-viewport seamless styling
    st.markdown(
        """
        <style>
            #MainMenu {visibility: hidden;}
            header[data-testid="stHeader"] { display: none !important; }
            div[data-testid="stToolbar"] { display: none !important; }
            footer { display: none !important; }
            [data-testid="stSidebar"] { display: none !important; }
            .main .block-container {
                padding: 0 !important;
                max-width: 100% !important;
                margin: 0 !important;
            }
            iframe {
                width: 100vw !important;
                height: 100vh !important;
                min-height: 100vh !important;
                border: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if _dist_dir.exists() and (_dist_dir / "index.html").exists():
        terminal_component = components.declare_component("trading_terminal", path=str(_dist_dir))
        terminal_component()
    else:
        st.error("Frontend build directory not found. Please run `npm run build` in `frontend/`.")


if __name__ == "__main__":
    main()
