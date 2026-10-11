"""
Financial Design System Tokens & CSS Theme.
Provides institutional dark styling, restrained accents, crisp contrast, and responsive grid layouts.
"""

from __future__ import annotations
import streamlit as st


def inject_custom_theme():
    """Inject institutional financial design styles into Streamlit."""
    st.markdown(
        """
        <style>
        /* Import clean Inter font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            letter-spacing: -0.011em;
        }

        /* Monospace for currency, strikes, and quantitative numbers */
        .metric-mono {
            font-family: 'JetBrains Mono', monospace;
            font-variant-numeric: tabular-nums;
        }

        /* App Background & Surfaces */
        .stApp {
            background-color: #090d16;
            color: #f1f5f9;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #0d121f;
            border-right: 1px solid #1e293b;
        }

        /* Hide duplicate default multipage nav */
        [data-testid="stSidebarNav"] {
            display: none !important;
        }

        /* Primary and Secondary Button Refinements */
        .stButton button {
            border-radius: 6px;
            font-weight: 500;
            font-size: 13px;
            transition: all 0.15s ease-in-out;
            border: 1px solid #334155;
        }

        .stButton button:hover {
            border-color: #64748b;
        }

        /* Metric Value Enhancements */
        [data-testid="stMetricValue"] {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.35rem !important;
            font-weight: 600;
            color: #f8fafc;
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.8rem !important;
            color: #94a3b8 !important;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* Cards and Containers */
        .fin-card {
            background-color: #111827;
            border: 1px solid #1f2937;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 14px;
        }

        .fin-card-interactive {
            background-color: #111827;
            border: 1px solid #1f2937;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 14px;
            transition: border-color 0.2s ease, transform 0.1s ease;
        }
        .fin-card-interactive:hover {
            border-color: #3b82f6;
        }

        /* Mode Badges */
        .mode-badge-beginner {
            background-color: #064e3b;
            color: #6ee7b7;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            display: inline-block;
        }

        .mode-badge-pro {
            background-color: #1e3a8a;
            color: #93c5fd;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            display: inline-block;
        }

        /* Educational Tooltip Box */
        .edu-tip-box {
            background-color: #1e293b;
            border-left: 3px solid #38bdf8;
            padding: 10px 14px;
            border-radius: 0 6px 6px 0;
            margin: 10px 0;
            font-size: 13px;
            color: #cbd5e1;
        }

        /* Financial Colors */
        .text-profit { color: #10b981 !important; font-weight: 600; }
        .text-loss { color: #ef4444 !important; font-weight: 600; }
        .text-muted { color: #94a3b8 !important; }

        /* Tables & DataFrames */
        .stDataFrame {
            border: 1px solid #1e293b;
            border-radius: 6px;
        }

        /* Form Inputs */
        .stTextInput input, .stNumberInput input, .stSelectbox select {
            border-radius: 6px;
            border: 1px solid #334155;
            background-color: #0f172a;
            color: #f8fafc;
        }

        /* Remove default clutter */
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        header { visibility: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )
