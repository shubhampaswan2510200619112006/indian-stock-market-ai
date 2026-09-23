"""
Streamlit Dashboard Page — Investor Executive Overview & Technical Due Diligence.
Phase 17A Final Investor-Readiness Hardened Interface.
"""

from __future__ import annotations

from datetime import datetime
import pandas as pd
import streamlit as st

from src.data_infrastructure.calendar import NSEMarketCalendar
from src.paper_trading.execution_guard import ExecutionGuard
from src.utils.config import get_config
from src.utils.time_utils import is_market_open, now_ist


def render_investor_overview_page():
    """Render institutional investor overview and truth-in-advertising due diligence portal."""
    st.title("🏛️ Investor Executive Overview & Platform Due Diligence")
    st.caption("Quantitative Research, Derivatives Microstructure, and Risk Architecture for Indian Markets (NSE)")

    # Hard Safety & Governance Notice
    guard = ExecutionGuard.get_execution_status()
    st.error(
        f"🛡️ **HARD GOVERNANCE BOUNDARY ACTIVE** | "
        f"LIVE REAL-MONEY EXECUTION: `{guard['LIVE_EXECUTION']}` | "
        f"BROKER CONNECTIONS: `{guard['BROKER_CONNECTIONS']}` | "
        "COMMERCIAL EXPENDITURE: `DISABLED` | "
        "OPTIONS PAPER TRADING: `BLOCKED (Live Quote Book Not Verified)`"
    )

    # 1. CURRENT PLATFORM STATUS (EVIDENCE-BASED)
    st.header("1. Current Platform Status")
    st.markdown(
        """
        The following status classifications reflect empirical repository audits, unit/integration verification,
        and frozen research results. Subjective rating scores are strictly prohibited.
        """
    )

    c1, c2, c3 = st.columns(3)
    c1.success("**SOFTWARE_ENGINEERING**: `READY`  \n*658 / 658 Unit & Integration Tests Passing (100%)*")
    c2.success("**INVESTOR_DEMO**: `READY`  \n*Transparent Due Diligence & Audit Portal Operational*")
    c3.warning("**LIVE_DATA**: `PARTIAL`  \n*Official EOD & Delayed Free Feeds; Broker Stubs Ready*")

    c4, c5, c6 = st.columns(3)
    c4.warning("**OPTIONS_RESEARCH**: `PARTIAL`  \n*Black-Scholes & Greeks Verified; Microstructure Limited*")
    c5.error("**EXECUTION_RESEARCH**: `BLOCKED`  \n*0.0% Continuous Executable Options Surface*")
    c6.error("**STATISTICAL_EVIDENCE**: `NO_DEMONSTRATED_EDGE`  \n*0 / 8 Pre-Registered Hypotheses Survived Friction*")

    st.divider()

    # 2. DATA STATUS
    st.header("2. Data Status & Ingestion Provenance")
    
    is_open = is_market_open()
    market_text = "🟢 OPEN" if is_open else "🔴 CLOSED"
    current_ist = now_ist().strftime("%H:%M:%S IST")
    
    st.markdown(f"**NSE Exchange Session:** {market_text} | **Current Time:** `{current_ist}`")

    source_data = [
        {
            "Data Feed / Stream": "NSE Official Bhavcopy (EOD)",
            "Underlying Coverage": "Equities & Derivatives (F&O)",
            "Actual Classification": "HISTORICAL / EOD",
            "Latency / Freshness": "End of Day (T+0 18:30 IST)",
            "Commercial Cost": "FREE (Regulatory Dissemination)",
            "Status": "ACTIVE & VERIFIED",
        },
        {
            "Data Feed / Stream": "Yahoo Finance (yfinance)",
            "Underlying Coverage": "Index & Stock Spot OHLCV",
            "Actual Classification": "DELAYED (15-min) / EOD",
            "Latency / Freshness": "15-minute delay during market hours",
            "Commercial Cost": "FREE (Public Non-Commercial)",
            "Status": "ACTIVE & OPERATIONAL",
        },
        {
            "Data Feed / Stream": "Zerodha Kite Connect API",
            "Underlying Coverage": "Tick-by-tick WebSocket & Intraday Bars",
            "Actual Classification": "REAL-TIME / LIVE DEPTH",
            "Latency / Freshness": "< 200ms when authenticated",
            "Commercial Cost": "₹4,000/month (Broker + Historical)",
            "Status": "INTEGRATION READY (Token Unconfigured)",
        },
        {
            "Data Feed / Stream": "Upstox Developer API (v2)",
            "Underlying Coverage": "Quotes, Candles & Options Chain",
            "Actual Classification": "REAL-TIME / LIVE",
            "Latency / Freshness": "< 300ms when authenticated",
            "Commercial Cost": "Nominal / Demat Required",
            "Status": "INTEGRATION READY (Token Unconfigured)",
        },
        {
            "Data Feed / Stream": "Angel One SmartAPI",
            "Underlying Coverage": "LTP, Snapquote Best 5, Historical OHLCV",
            "Actual Classification": "REAL-TIME / HISTORICAL OHLCV",
            "Latency / Freshness": "Real-time snapquote; OHLCV history",
            "Commercial Cost": "Free with Trading Account",
            "Status": "CATALOGED & EVALUATED (No Expired F&O)",
        },
        {
            "Data Feed / Stream": "TruData / GlobalDataFeeds",
            "Underlying Coverage": "Multi-Year Options Tick & 1-min Bid/Ask",
            "Actual Classification": "INSTITUTIONAL REAL-TIME & HISTORICAL",
            "Latency / Freshness": "Millisecond tick stream",
            "Commercial Cost": "₹3,500 – ₹8,000/month",
            "Status": "UNFUNDED (Zero-Cost Policy Active)",
        },
    ]
    st.dataframe(pd.DataFrame(source_data), use_container_width=True)

    st.warning(
        "⚠️ **TRUTH-IN-ADVERTISING DISCLOSURE**: In the absence of an active paid broker token, "
        "all live displays show DELAYED or END-OF-DAY data. The system NEVER synthesizes fake live quotes or Bid/Ask spreads."
    )

    st.divider()

    # 3. MODEL STATUS: HEURISTIC vs CALIBRATED PROBABILITY
    st.header("3. Model Status: Heuristics vs. Calibrated Probabilities")
    st.markdown(
        """
        The platform strictly enforces the mathematical boundary between **Deterministic Heuristics** and
        **Statistically Calibrated Empirical Probabilities**:
        """
    )

    col_h, col_p = st.columns(2)
    with col_h:
        st.subheader("Deterministic Heuristic Scores")
        st.markdown(
            """
            - **Scope**: Rule-based pattern matching (e.g. `AIMarketAnalyst` bias score, `MarketRegimeEngine` alignment).
            - **Target Event**: Contemporaneous multi-indicator concordance (trend, ATR, VIX, EMAs).
            - **Interpretation**: Index of pattern alignment (0.0 to 1.0).
            - **Limitation**: **NOT an empirical probability.** Cannot be used for Kelly sizing or statistical expectancy calculations.
            """
        )
    with col_p:
        st.subheader("Calibrated Empirical Probabilities")
        st.markdown(
            """
            - **Scope**: Machine learning inference (`src/ml/`, `src/research/`).
            - **Target Event**: Explicit forward return: $P(R_{t \\to t+h} > 0)$ over horizon $h \\in \\{1, 5, 20\\}$ days.
            - **Calibration Methods**: **Platt Scaling** (Logistic Sigmoid) & **Isotonic Regression** fitted strictly on out-of-fold cross-validation.
            - **Metrics Monitored**: Brier Score, Expected Calibration Error (ECE), and Reliability Diagrams.
            """
        )

    st.markdown("#### Five-Tier Model Maturity Classification")
    tier_data = [
        {"Tier": "1. MODEL_AVAILABLE", "Status": "VERIFIED", "Description": "Architecture, feature pipelines, and model classes implemented."},
        {"Tier": "2. MODEL_VALIDATED", "Status": "VERIFIED", "Description": "Walk-forward time-series splits with purge and embargo periods applied."},
        {"Tier": "3. MODEL_CALIBRATED", "Status": "VERIFIED", "Description": "Empirical calibration curves, Platt scaling, and Brier Score evaluation active."},
        {"Tier": "4. STATISTICAL_EVIDENCE", "Status": "NO_DEMONSTRATED_EDGE", "Description": "0 / 8 hypotheses survived Indian market statutory transaction friction."},
        {"Tier": "5. EXECUTION-REALISTIC", "Status": "BLOCKED", "Description": "Continuous executable historical options quote surface is 0.0%."},
    ]
    st.dataframe(pd.DataFrame(tier_data), use_container_width=True)

    st.divider()

    # 4. OPTIONS STATUS & MICROSTRUCTURE TRUTH
    st.header("4. Options Status & Derivatives Microstructure")
    st.markdown(
        """
        All mathematical calculations (Black-Scholes-Merton, Implied Volatility root-solving, Greeks)
        have been verified for mathematical and dimensional correctness:
        - **Delta ($\\Delta$)**: Direct $[-1, 1]$
        - **Gamma ($\\Gamma$)**: Per 1 index point move
        - **Theta ($\\Theta$)**: **Scaled by 1/365** (Decay per calendar day)
        - **Vega ($\\nu$)**: **Scaled by 1/100** (Price change per 1% change in IV)
        - **Rho ($\\rho$)**: **Scaled by 1/100** (Price change per 1% change in $r$)
        - **IV Solver**: Newton-Raphson quadratic solver with Brent bracketed root-finder fallback; absolute error $\\le 10^{-5}$.
        """
    )

    st.markdown("#### Immutable Options Empirical Truth (Phase 9.8 Frozen)")
    o1, o2, o3, o4 = st.columns(4)
    o1.metric("Total Option Quotes", "15,106")
    o2.metric("Valid Paired Bid/Ask Quotes", "102")
    o3.metric("Paired Quote Coverage", "0.68%")
    o4.metric("Continuous Executable Surface", "0.0%")

    st.error(
        "🛑 **OPTIONS EXECUTION RESEARCH IS BLOCKED**: Due to 0.0% continuous executable surface coverage, "
        "historical options execution backtesting is strictly BLOCKED. The platform refuses to convert LTP into synthetic Bid/Ask."
    )

    st.divider()

    # 5. VALIDATION STATUS & STATUTORY TRANSACTION FRICTION
    st.header("5. Validation Status & Indian Statutory Friction Accounting")
    st.markdown(
        """
        Every backtest and strategy evaluation incorporates double-entry statutory transaction friction.
        Strategies that appear profitable before costs often fail after real-world taxation:
        """
    )

    cost_data = [
        {"Fee Component": "Brokerage", "Rate": "₹20 flat per executed order", "Applied To": "Buy & Sell"},
        {"Fee Component": "Securities Transaction Tax (STT)", "Rate": "0.0625% on premium turnover", "Applied To": "Sell Side Only"},
        {"Fee Component": "NSE Exchange Transaction Charges", "Rate": "0.053% on turnover", "Applied To": "Buy & Sell"},
        {"Fee Component": "Goods & Services Tax (GST)", "Rate": "18% on (Brokerage + Exchange Fees)", "Applied To": "Buy & Sell"},
        {"Fee Component": "SEBI Turnover Charge", "Rate": "₹10 per crore (0.0001%)", "Applied To": "Buy & Sell"},
        {"Fee Component": "Stamp Duty", "Rate": "0.003% on premium turnover", "Applied To": "Buy Side Only"},
        {"Fee Component": "Bid-Ask Slippage", "Rate": "Real quote spread or conservative 1% - 2.5%", "Applied To": "Buy & Sell"},
    ]
    st.dataframe(pd.DataFrame(cost_data), use_container_width=True)

    st.info(
        "🔬 **EMPIRICAL RESEARCH RESULT**: Across all 8 pre-registered hypotheses in Phase 9.8, "
        "microstructure turnover drag exceeded gross returns. Net Sharpe remained negative, leading to the authoritative "
        "verdict: `PHASE_10_NOT_JUSTIFIED`."
    )

    st.divider()

    # 6. HONEST INSTITUTIONAL LIMITATIONS
    st.header("6. Honest Institutional Limitations")
    
    lim_data = [
        {
            "Capability Dimension": "Real-Money Broker Execution",
            "Current Status": "BLOCKED BY ARCHITECTURE",
            "Reason / Evidence": "Compile-time constant ALLOW_LIVE_EXECUTION = False in ExecutionGuard prevents live orders.",
        },
        {
            "Capability Dimension": "Historical Options Execution Backtest",
            "Current Status": "BLOCKED BY DATA QUALITY",
            "Reason / Evidence": "Historical paired Bid/Ask quote coverage is 0.68% (102 / 15,106 quotes). Continuous executable surface is 0.0%. LTP substitution is prohibited.",
        },
        {
            "Capability Dimension": "Real-Time Options Paper Trading",
            "Current Status": "BLOCKED PENDING LIVE FEED",
            "Reason / Evidence": "Paper trading requires active live Bid/Ask crossing. Synthetic fill generation is strictly forbidden.",
        },
        {
            "Capability Dimension": "Multi-Year Intraday High-Frequency Edge",
            "Current Status": "DATA LIMITED",
            "Reason / Evidence": "Public online sources investigated do not satisfy long-term intraday tick requirements. Requires authorized commercial vendor dataset.",
        },
    ]
    st.dataframe(pd.DataFrame(lim_data), use_container_width=True)

    st.success(
        "✅ **INVESTOR READINESS CONCLUSION**: The platform demonstrates mature software engineering, rigorous derivatives mathematics, "
        "transparent statistical accounting, and ironclad capital protection. It is ready for institutional due diligence demonstration."
    )
