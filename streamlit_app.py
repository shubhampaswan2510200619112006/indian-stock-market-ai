"""
Streamlit Cloud Entrypoint for Indian Stock Market AI.

Delegates execution directly to dashboard/app.py for seamless root detection
on Streamlit Community Cloud, Railway, Render, Docker, and local execution.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure root directory is in sys.path
_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from dashboard.app import main

if __name__ == "__main__":
    main()
