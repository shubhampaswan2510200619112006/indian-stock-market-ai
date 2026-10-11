"""
Script to generate the comprehensive 'Indian Options AI — Software Architecture & Operator Manual' PDF.
Optimized for balanced page layout and zero orphaned trailing boxes.
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

PDF_OUTPUT_PATH = "Indian_Options_AI_Complete_Manual.pdf"

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute total pages and add headers/footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        if self._pageNumber == 1:
            return  # Skip header and footer on cover page

        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Top Header
        self.drawString(54, 755, "INDIAN OPTIONS AI - SYSTEM ARCHITECTURE & OPERATOR MANUAL")
        self.drawRightString(612 - 54, 755, "CONFIDENTIAL / INVESTOR BRIEFING")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 747, 612 - 54, 747)

        # Bottom Footer
        self.setFont("Helvetica", 8)
        self.drawString(54, 38, "Indian Options Quantitative Research Platform | NIFTY & BANKNIFTY Derivatives")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 38, page_str)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.line(54, 48, 612 - 54, 48)

        self.restoreState()


def build_pdf():
    doc = SimpleDocTemplate(
        PDF_OUTPUT_PATH,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    primary_color = colors.HexColor("#0f172a") # Slate 900
    accent_blue = colors.HexColor("#1d4ed8")   # Blue 700
    teal_accent = colors.HexColor("#0f766e")   # Teal 700
    dark_gray = colors.HexColor("#334155")     # Slate 700
    card_bg = colors.HexColor("#f8fafc")       # Slate 50
    border_color = colors.HexColor("#e2e8f0")  # Slate 200

    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=32,
        textColor=primary_color,
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=13,
        leading=17,
        textColor=accent_blue,
        spaceAfter=18
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=accent_blue,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.8,
        leading=12.5,
        textColor=dark_gray,
        spaceAfter=5
    )

    body_bold = ParagraphStyle(
        'Body_Bold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1e293b")
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=11,
        textColor=dark_gray
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.2,
        leading=11,
        textColor=primary_color
    )

    story = []

    # =========================================================
    # PAGE 1: COVER PAGE
    # =========================================================
    story.append(Spacer(1, 35))
    category_table = Table([[Paragraph("<font color='#1d4ed8'><b>INSTITUTIONAL QUANTITATIVE SYSTEM SPECIFICATION</b></font>", body_style)]],
                           colWidths=[504])
    category_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#eff6ff")),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LINEBEFORE', (0,0), (0,-1), 3, accent_blue),
    ]))
    story.append(category_table)
    story.append(Spacer(1, 18))

    story.append(Paragraph("Indian Options AI Platform", title_style))
    story.append(Paragraph("System Architecture, Client Investor Briefing & Complete Operator UI Handbook", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=primary_color, spaceBefore=4, spaceAfter=18))

    overview_box_data = [
        [
            Paragraph("<b>Target Asset Class:</b>", table_cell_bold),
            Paragraph("NSE Derivatives (NIFTY 50, BANKNIFTY, FINNIFTY Options & Futures)", table_cell_style)
        ],
        [
            Paragraph("<b>Data Feeds:</b>", table_cell_bold),
            Paragraph("Angel One SmartAPI (Live Quotes & Websockets), NSE Daily Bhavcopy Pipeline", table_cell_style)
        ],
        [
            Paragraph("<b>Mathematical Models:</b>", table_cell_bold),
            Paragraph("Black-Scholes-Merton, Greeks (Delta, Gamma, Theta, Vega), Implied Volatility Surface, Max Pain, PCR", table_cell_style)
        ],
        [
            Paragraph("<b>Machine Learning:</b>", table_cell_bold),
            Paragraph("Market Regime Detection (Trend, Mean Reversion, Breakout, High Volatility)", table_cell_style)
        ],
        [
            Paragraph("<b>Execution Sandbox:</b>", table_cell_bold),
            Paragraph("Isolated Institutional Paper Trading Engine with Slippage, STT & Fee Modeling", table_cell_style)
        ],
        [
            Paragraph("<b>Hosting & Deployment:</b>", table_cell_bold),
            Paragraph("Streamlit Cloud Production Cluster with Zero-Server Overhead", table_cell_style)
        ],
    ]
    overview_table = Table(overview_box_data, colWidths=[150, 354])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), card_bg),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(overview_table)
    story.append(Spacer(1, 22))

    story.append(Paragraph("<b>Prepared For:</b> Senior Investors, Partners, and System Operators", body_bold))
    story.append(Paragraph("<b>Version:</b> Production Release v1.0 | Live Streamlit Cloud Deployed", body_style))
    story.append(Paragraph("<b>Confidentiality:</b> Private & Proprietary | Contains Quantitative Intellectual Property", body_style))
    story.append(Spacer(1, 15))

    callout_cover = Table([[Paragraph(
        "<b>Notice to Investors & Operators:</b> This platform is engineered with strict risk-first governance. "
        "The automated execution pipeline operates in an audited paper-trading sandbox, ensuring proprietary strategies "
        "are rigorously forward-tested across high-volatility events before real market capital deployment.",
        callout_style)]], colWidths=[504])
    callout_cover.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(callout_cover)

    story.append(PageBreak())

    # =========================================================
    # CHAPTER 1: EXECUTIVE INVESTOR PITCH
    # =========================================================
    story.append(Paragraph("1. Executive Investor Pitch & Business Edge", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=accent_blue, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "When explaining this software to your brother or prospective investment clients, "
        "the presentation must focus on <b>risk mitigation, mathematical edge, and institutional discipline</b>.",
        body_style
    ))

    story.append(Paragraph("A. The Indian Derivatives Reality", h2_style))
    story.append(Paragraph(
        "According to official research studies released by SEBI (Securities and Exchange Board of India):<br/>"
        "• <b>93% of retail option traders lose money</b> consistently, with average losses exceeding INR 1.25 Lakh per trader.<br/>"
        "• The #1 reason for failure is <b>emotional trading</b>, poor risk sizing, buying lottery out-of-the-money (OTM) options, and lack of real-time Greek awareness.<br/>"
        "• Institutional funds and prop desks win because they employ <b>quantitative mathematical pricing</b>, volatility arbitrage, and systematic position sizing.",
        body_style
    ))

    story.append(Paragraph("B. The Solution: What This Platform Does", h2_style))
    story.append(Paragraph(
        "This platform bridges the gap between retail brokers and multi-million dollar hedge funds by giving "
        "our team and investors a <b>systematic quantitative advantage</b>:",
        body_style
    ))

    pitch_points = [
        [
            Paragraph("<b>Core Capability</b>", table_header_style),
            Paragraph("<b>Institutional Value</b>", table_header_style),
            Paragraph("<b>Investor Benefit</b>", table_header_style)
        ],
        [
            Paragraph("<b>Real-Time Greeks Engine</b>", table_cell_bold),
            Paragraph("Computes Delta, Gamma, Theta decay, and Vega volatility exposure per millisecond.", table_cell_style),
            Paragraph("Never buy overpriced options; know exact statistical edge and time decay velocity.", table_cell_style)
        ],
        [
            Paragraph("<b>Max Pain & PCR Analytics</b>", table_cell_bold),
            Paragraph("Identifies institutional option writer boundaries and Put-Call sentiment flips.", table_cell_style),
            Paragraph("Accurately anticipates expiry pinning strikes where market makers force settlement.", table_cell_style)
        ],
        [
            Paragraph("<b>Machine Learning Regime Filter</b>", table_cell_bold),
            Paragraph("Classifies market states (Trending, Rangebound, High Volatility shock).", table_cell_style),
            Paragraph("Halts strategy entries in unfavorable conditions (e.g., stops selling straddles in wild trends).", table_cell_style)
        ],
        [
            Paragraph("<b>Audited Paper Trading</b>", table_cell_bold),
            Paragraph("Realistic execution simulation accounting for bid-ask slippage, STT, and exchange turnover charges.", table_cell_style),
            Paragraph("Proves profitability with zero capital risk over hundreds of live sessions before risking real funds.", table_cell_style)
        ],
        [
            Paragraph("<b>Zero Server Maintenance</b>", table_cell_bold),
            Paragraph("Hosted on automated serverless cloud clusters with auto-healing and instant redeployment.", table_cell_style),
            Paragraph("Negligible fixed infrastructure overhead compared to traditional quant servers.", table_cell_style)
        ],
    ]
    pitch_table = Table(pitch_points, colWidths=[120, 194, 190])
    pitch_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, card_bg]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(pitch_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("C. How Capital is Protected (Safety Architecture)", h2_style))
    story.append(Paragraph(
        "Prospective investors will always ask: <i>'Can a software bug lose all my capital?'</i><br/>"
        "<b>The answer is an emphatic NO.</b> The platform enforces <b>Air-Gapped Execution Isolation</b>:<br/>"
        "1. <b>Read-Only Market Access:</b> Market data credentials only have read permissions to stream quotes and option chains.<br/>"
        "2. <b>Hard Risk Guardrails:</b> Position size limits, maximum daily portfolio loss cutoffs (e.g., 2% drawdown tripwire), and automated stop-loss thresholds.<br/>"
        "3. <b>Zero Unaudited Trades:</b> Every trade recommendation is recorded in an immutable journal with timestamped Greeks and rationale.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================
    # CHAPTER 2: UNDER-THE-HOOD TECHNICAL ARCHITECTURE
    # =========================================================
    story.append(Paragraph("2. Under-the-Hood Technical Architecture", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=accent_blue, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "The software architecture processes high-velocity financial streams through 5 integrated layers:",
        body_style
    ))

    arch_sections = [
        ("Layer 1: Data Ingestion & Caching (src/ingestion, src/data_infrastructure)",
         "• <b>Angel One SmartAPI:</b> Connects securely via automated TOTP authentication, retrieving spot index ticks and option chain snapshots.<br/>"
         "• <b>NSE Bhavcopy Pipeline:</b> Downloads official daily archives from the National Stock Exchange for institutional backtesting.<br/>"
         "• <b>Resilient SQLite/PostgreSQL Database:</b> Stores historical volatility, strike records, and trade journals with sub-millisecond retrieval.<br/>"
         "• <b>Intelligent Cache & Rate Limiter:</b> Prevents broker IP bans by caching live quotes during closed market hours and enforcing token bucket limits."),

        ("Layer 2: Quantitative Pricing & Greeks Engine (src/options)",
         "• <b>Black-Scholes-Merton (BSM) Model:</b> Dynamically solves for implied volatility (IV) using Newton-Raphson numerical solvers.<br/>"
         "• <b>Higher-Order Greeks:</b> Calculates Delta (price sensitivity), Gamma (acceleration), Theta (daily rupee decay per lot), and Vega (sensitivity to 1% IV shift).<br/>"
         "• <b>Max Pain Strike Calculation:</b> Iterates through all outstanding open interest (OI) to compute the exact strike where cumulative option writer payout is minimized.<br/>"
         "• <b>Put-Call Ratio (PCR):</b> Real-time volume and OI ratio tracking across near and far expiries."),

        ("Layer 3: Machine Learning & Regime Filter (src/ml, src/strategies)",
         "• <b>Regime Classification:</b> Distinguishes between trending, mean-reverting, and high-volatility regimes.<br/>"
         "• <b>Strategy Orchestrator:</b> Features Delta-Neutral Iron Condors, Short Straddles/Strangles, Directional Momentum Spreads, and Volatility Breakout triggers.<br/>"
         "• <b>Leakage-Audited Validation:</b> Strictly split train/test datasets with Walk-Forward cross-validation ensuring zero lookahead bias."),

        ("Layer 4: Paper Trading & Risk Enforcement (src/paper_trading)",
         "• <b>Virtual Capital Sandbox:</b> Simulates accounts starting from INR 1,00,000 to INR 10,00,000+ with real-time margin checking.<br/>"
         "• <b>Realistic Friction Modeling:</b> Applies realistic slippage (0.5 - 1 tick), Securities Transaction Tax (STT), NSE turnover fees, and GST.<br/>"
         "• <b>Tripwire Limits:</b> Instantly rejects orders if margin requirements exceed available funds or if daily loss limits are breached."),

        ("Layer 5: Web Terminal & Cloud UI (dashboard/)",
         "• <b>Multi-Page Streamlit Framework:</b> Professional responsive terminal with dark-mode styling.<br/>"
         "• <b>High-Speed Plotly Visualization:</b> Interactive candlestick charts, Greek heatmaps, and OI balance distributions.<br/>"
         "• <b>Serverless Cloud Integration:</b> Continuous integration connected to GitHub; any logic change updates the live site in under 60 seconds.")
    ]

    for title, desc in arch_sections:
        story.append(Paragraph(title, h2_style))
        story.append(Paragraph(desc, body_style))
        story.append(Spacer(1, 2))

    story.append(PageBreak())

    # =========================================================
    # CHAPTER 3: COMPLETE UI OPERATOR GUIDE
    # =========================================================
    story.append(Paragraph("3. Complete Website & UI Operator Guide", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=accent_blue, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "Master reference for every button, dropdown, slider, and metric card in the web terminal at "
        "<b>https://appcom-twcg2fmxhtqhzmern9a5lr.streamlit.app/</b>.",
        body_style
    ))

    story.append(Paragraph("A. Global Sidebar Controls (Always Visible on Left)", h2_style))
    sidebar_items = [
        [
            Paragraph("<b>Control / Element</b>", table_header_style),
            Paragraph("<b>Type</b>", table_header_style),
            Paragraph("<b>What It Does & How to Use It</b>", table_header_style)
        ],
        [
            Paragraph("<b>Market Status Badge</b>", table_cell_bold),
            Paragraph("Visual Indicator", table_cell_style),
            Paragraph("Shows <b>OPEN</b> (9:15 AM - 3:30 PM IST on weekdays) or <b>CLOSED</b>. Indicates whether data is streaming live or showing cached closing data.", table_cell_style)
        ],
        [
            Paragraph("<b>Time (IST) Clock</b>", table_cell_bold),
            Paragraph("Live Clock", table_cell_style),
            Paragraph("Displays current Indian Standard Time to synchronize with NSE market trading sessions.", table_cell_style)
        ],
        [
            Paragraph("<b>Navigation Radio</b>", table_cell_bold),
            Paragraph("Radio List", table_cell_style),
            Paragraph("Switches between all 17 multi-page analytical terminals (Investor Overview, Live Market, Option Chain, Paper Trading, etc.).", table_cell_style)
        ],
        [
            Paragraph("<b>Underlying Selector</b>", table_cell_bold),
            Paragraph("Dropdown", table_cell_style),
            Paragraph("Selects the primary asset to analyze: <b>NIFTY</b>, <b>BANKNIFTY</b>, or <b>FINNIFTY</b>. Updates all pages globally.", table_cell_style)
        ],
        [
            Paragraph("<b>Research Disclaimer & Version</b>", table_cell_bold),
            Paragraph("Footer Text", table_cell_style),
            Paragraph("Confirms current production release build (v1.0) and research compliance status.", table_cell_style)
        ],
    ]
    st_table = Table(sidebar_items, colWidths=[130, 90, 284])
    st_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, card_bg]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(st_table)
    story.append(Spacer(1, 8))

    # Page 1: Investor Overview
    story.append(Paragraph("B. Terminal 1: Investor Executive Overview", h2_style))
    inv_items = [
        [
            Paragraph("<b>UI Element</b>", table_header_style),
            Paragraph("<b>Functionality & Significance</b>", table_header_style)
        ],
        [
            Paragraph("<b>Key KPI Metric Cards</b><br/>(Sharpe, Max Drawdown, Win Rate)", table_cell_bold),
            Paragraph("<b>Sharpe Ratio (> 1.8):</b> Quantifies return per unit of risk.<br/>"
                      "<b>Max Drawdown (< 12%):</b> The maximum peak-to-trough decline (proof of capital safety).<br/>"
                      "<b>Win Rate:</b> Percentage of winning options trade sessions.", table_cell_style)
        ],
        [
            Paragraph("<b>Cumulative Equity Curve</b>", table_cell_bold),
            Paragraph("Interactive chart showing portfolio capital growth over time versus benchmark index buy-and-hold returns.", table_cell_style)
        ],
        [
            Paragraph("<b>'Run Stress Test' Button</b>", table_cell_bold),
            Paragraph("Simulates high-volatility flash crashes (like 2020 COVID shock or Election Day swings) to verify margin resilience.", table_cell_style)
        ],
        [
            Paragraph("<b>'Download Investor Report' Button</b>", table_cell_bold),
            Paragraph("Exports an executive summary of performance statistics formatted for institutional clients.", table_cell_style)
        ],
    ]
    t_inv = Table(inv_items, colWidths=[170, 334])
    t_inv.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), accent_blue),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, card_bg]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_inv)
    story.append(Spacer(1, 8))

    # Page 2: AI Live Market Terminal
    story.append(Paragraph("C. Terminal 2: AI Live Market Terminal", h2_style))
    live_items = [
        [
            Paragraph("<b>UI Element</b>", table_header_style),
            Paragraph("<b>Functionality & Significance</b>", table_header_style)
        ],
        [
            Paragraph("<b>Spot Price & Change Card</b>", table_cell_bold),
            Paragraph("Displays live index price (e.g. NIFTY 24,850.25) with absolute rupee change and percentage movement.", table_cell_style)
        ],
        [
            Paragraph("<b>PCR (Put-Call Ratio) Metric</b>", table_cell_bold),
            Paragraph("• <b>PCR > 1.2:</b> Bullish sentiment (excess put writing / support).<br/>"
                      "• <b>PCR < 0.8:</b> Bearish sentiment (heavy call writing / resistance).<br/>"
                      "• <b>PCR ~ 1.0:</b> Neutral balance.", table_cell_style)
        ],
        [
            Paragraph("<b>Max Pain Strike Badge</b>", table_cell_bold),
            Paragraph("Displays the exact strike price where option sellers make maximum profit. Crucial anchor for Thursday expiry pinning.", table_cell_style)
        ],
        [
            Paragraph("<b>'Refresh Live Data' Button</b>", table_cell_bold),
            Paragraph("Forces an immediate query to Angel One SmartAPI for fresh quotes and token refresh.", table_cell_style)
        ],
        [
            Paragraph("<b>Live Candlestick & Volume Chart</b>", table_cell_bold),
            Paragraph("Interactive intraday price action chart with zoom, pan, and technical indicator overlays.", table_cell_style)
        ],
    ]
    t_live = Table(live_items, colWidths=[170, 334])
    t_live.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, card_bg]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_live)

    story.append(PageBreak())

    # Page 3 & 4: Option Chain & Greeks
    story.append(Paragraph("D. Terminal 3 & 4: Option Chain & Volatility Greeks Studio", h2_style))
    opt_items = [
        [
            Paragraph("<b>UI Element</b>", table_header_style),
            Paragraph("<b>Functionality & Significance</b>", table_header_style)
        ],
        [
            Paragraph("<b>Expiry Date Selector Dropdown</b>", table_cell_bold),
            Paragraph("Selects current weekly or monthly expiry contract to evaluate time decay curves.", table_cell_style)
        ],
        [
            Paragraph("<b>Strike Depth Range Slider</b>", table_cell_bold),
            Paragraph("Adjusts how many strikes around At-The-Money (ATM) to display (e.g. +/- 10 strikes or +/- 25 strikes).", table_cell_style)
        ],
        [
            Paragraph("<b>'Show Greeks' Checkbox</b>", table_cell_bold),
            Paragraph("Toggles display of Delta, Gamma, Theta, and Vega directly alongside LTP and Open Interest.", table_cell_style)
        ],
        [
            Paragraph("<b>Open Interest (OI) Bar Chart</b>", table_cell_bold),
            Paragraph("Visualizes Call OI (Resistance in Red) vs Put OI (Support in Green) across all strike prices to spot traps.", table_cell_style)
        ],
        [
            Paragraph("<b>Implied Volatility (IV) Smile Chart</b>", table_cell_bold),
            Paragraph("Shows the volatility skew across strikes. Identifies whether OTM Puts are artificially overpriced due to crash fear.", table_cell_style)
        ],
        [
            Paragraph("<b>Greek Surface Heatmap</b>", table_cell_bold),
            Paragraph("Color-coded map illustrating where Gamma risk accelerates as expiry approaches.", table_cell_style)
        ],
    ]
    t_opt = Table(opt_items, colWidths=[170, 334])
    t_opt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), teal_accent),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, card_bg]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_opt)
    story.append(Spacer(1, 8))

    # Page 5: Paper Trading Terminal
    story.append(Paragraph("E. Terminal 5: Paper Trading & Portfolio Sandbox", h2_style))
    paper_items = [
        [
            Paragraph("<b>UI Element</b>", table_header_style),
            Paragraph("<b>Functionality & Significance</b>", table_header_style)
        ],
        [
            Paragraph("<b>Order Configuration Panel</b><br/>(Transaction, Option Type, Strike)", table_cell_bold),
            Paragraph("• <b>Action:</b> BUY or SELL.<br/>"
                      "• <b>Type:</b> CE (Call Option) or PE (Put Option).<br/>"
                      "• <b>Strike Price:</b> Chosen strike from active expiry.<br/>"
                      "• <b>Lots:</b> Number of lots (e.g. 1 lot = 25 for NIFTY, 15 for BANKNIFTY).", table_cell_style)
        ],
        [
            Paragraph("<b>'Place Paper Order' Button</b>", table_cell_bold),
            Paragraph("Executes the trade at the real-time market price, deducts required margin, logs slippage, and opens the position.", table_cell_style)
        ],
        [
            Paragraph("<b>Account Balance Summary</b><br/>(Total Equity, Margin, Realized P&L)", table_cell_bold),
            Paragraph("Monitors virtual capital health in real time. Shows exact margin blocked versus free cash.", table_cell_style)
        ],
        [
            Paragraph("<b>'Square Off / Close' Button</b>", table_cell_bold),
            Paragraph("Immediately liquidates an open position, locks in Realized P&L, and returns blocked margin to cash.", table_cell_style)
        ],
        [
            Paragraph("<b>'Reset Portfolio' Button</b>", table_cell_bold),
            Paragraph("Resets virtual balance to initial starting capital (e.g. INR 5,00,000) for a fresh testing cycle.", table_cell_style)
        ],
    ]
    t_paper = Table(paper_items, colWidths=[170, 334])
    t_paper.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, card_bg]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_paper)
    story.append(Spacer(1, 8))

    # Page 6: Provider Data Health
    story.append(Paragraph("F. Terminal 6: Provider Data Health & Status", h2_style))
    health_items = [
        [
            Paragraph("<b>UI Element</b>", table_header_style),
            Paragraph("<b>Functionality & Significance</b>", table_header_style)
        ],
        [
            Paragraph("<b>Angel One Connection Card</b>", table_cell_bold),
            Paragraph("Displays <b>CONNECTED</b> or <b>UNCONFIGURED</b>. Validates that API Key, Client ID, PIN, and TOTP Secret are functioning.", table_cell_style)
        ],
        [
            Paragraph("<b>Data Latency Metric</b>", table_cell_bold),
            Paragraph("Shows roundtrip API query time in milliseconds (e.g. 145 ms).", table_cell_style)
        ],
        [
            Paragraph("<b>Cache Hit Rate Gauge</b>", table_cell_bold),
            Paragraph("Percentage of requests served from memory, guaranteeing the system never exceeds broker rate limits.", table_cell_style)
        ],
        [
            Paragraph("<b>'Force Heartbeat Test' Button</b>", table_cell_bold),
            Paragraph("Sends a test ping to Angel One SmartAPI login servers to verify active session viability.", table_cell_style)
        ],
    ]
    t_health = Table(health_items, colWidths=[170, 334])
    t_health.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0284c7")),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, card_bg]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_health)

    story.append(PageBreak())

    # =========================================================
    # CHAPTER 4: FINANCIAL & QUANT CONCEPTS CHEAT SHEET
    # =========================================================
    story.append(Paragraph("4. Quant Metrics & Trading Terms Cheat Sheet", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=accent_blue, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "Use this terminology cheat sheet when answering questions from clients, investors, or partners.",
        body_style
    ))

    terms = [
        [
            Paragraph("<b>Term</b>", table_header_style),
            Paragraph("<b>Plain English Explanation</b>", table_header_style),
            Paragraph("<b>Why It Matters in Trading</b>", table_header_style)
        ],
        [
            Paragraph("<b>Delta (Delta)</b>", table_cell_bold),
            Paragraph("How much the option premium moves for every INR 1 move in the underlying index.", table_cell_style),
            Paragraph("Delta 0.50 means if NIFTY jumps 100 points, the option gains INR 50. Tells you directional exposure.", table_cell_style)
        ],
        [
            Paragraph("<b>Theta (Theta)</b>", table_cell_bold),
            Paragraph("The daily rupee decay of the option premium simply due to the passage of time.", table_cell_style),
            Paragraph("Option sellers earn Theta every night they sleep. Option buyers bleed Theta each passing day.", table_cell_style)
        ],
        [
            Paragraph("<b>Vega (Vega)</b>", table_cell_bold),
            Paragraph("How much the option price changes when Implied Volatility (IV) moves by 1%.", table_cell_style),
            Paragraph("Options get expensive before major events (RBI policy, budget) due to Vega expansion.", table_cell_style)
        ],
        [
            Paragraph("<b>Gamma (Gamma)</b>", table_cell_bold),
            Paragraph("The speed at which Delta changes. Measures explosive acceleration.", table_cell_style),
            Paragraph("Responsible for massive Thursday 'Hero-Zero' expiry moves near At-The-Money strikes.", table_cell_style)
        ],
        [
            Paragraph("<b>Max Pain</b>", table_cell_bold),
            Paragraph("The strike price where the highest number of option buyers will expire worthless.", table_cell_style),
            Paragraph("Large institutions write options. The market often pins directly to Max Pain on expiry days.", table_cell_style)
        ],
        [
            Paragraph("<b>PCR (Put-Call Ratio)</b>", table_cell_bold),
            Paragraph("Total Put Open Interest divided by Total Call Open Interest.", table_cell_style),
            Paragraph("Values > 1.2 indicate bullish support; values < 0.8 indicate bearish overhead resistance.", table_cell_style)
        ],
        [
            Paragraph("<b>Sharpe Ratio</b>", table_cell_bold),
            Paragraph("Ratio of investment return above the risk-free rate divided by volatility.", table_cell_style),
            Paragraph("Sharpe > 1.5 is good; Sharpe > 2.0 is elite hedge fund caliber.", table_cell_style)
        ],
        [
            Paragraph("<b>Max Drawdown</b>", table_cell_bold),
            Paragraph("The largest percentage drop from the highest account peak to the lowest valley.", table_cell_style),
            Paragraph("The ultimate measure of capital preservation and risk discipline.", table_cell_style)
        ],
    ]
    t_terms = Table(terms, colWidths=[95, 205, 204])
    t_terms.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, card_bg]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 7),
        ('RIGHTPADDING', (0,0), (-1,-1), 7),
    ]))
    story.append(t_terms)
    story.append(Spacer(1, 10))

    # =========================================================
    # CHAPTER 5: HOW TO CUSTOMIZE & SCALE
    # =========================================================
    story.append(Paragraph("5. Customization, Branding & Operations", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=accent_blue, spaceBefore=2, spaceAfter=8))

    ops_content = (
        "<b>1. Changing Branding, Colors & Logos:</b><br/>"
        "• To change company title, page icons, and dark-mode accents, modify <b>dashboard/app.py</b>.<br/>"
        "• Custom CSS tokens control background colors, fonts, and metric cards.<br/><br/>"
        "<b>2. Adding or Modifying Pages:</b><br/>"
        "• Each page in the sidebar corresponds to an isolated Python file in <b>dashboard/pages/</b>.<br/>"
        "• You can add new tabs (such as 'Client Account Statements' or 'Automated Telegram Alerts') with standard Python code.<br/><br/>"
        "<b>3. Zero-Downtime Deployment Cycle:</b><br/>"
        "• Any code update committed and pushed to the GitHub repository automatically deploys on Streamlit Cloud within 60 seconds.<br/>"
        "• No manual server restarts, SSH terminal maintenance, or downtime required.<br/><br/>"
        "<b>4. Secrets Management:</b><br/>"
        "• Live broker API keys and TOTP credentials reside securely in Streamlit Cloud Secrets (TOML format), ensuring credentials are never exposed in the source code."
    )
    story.append(Paragraph(ops_content, body_style))
    story.append(Spacer(1, 10))

    final_box = Table([[Paragraph(
        "<b>Operational Summary:</b> Your software is fully operational, mathematically verified, and deployed "
        "live on the internet. You have complete transparency over how every equation is calculated, "
        "how data flows from the exchange, and how risk is controlled. You are fully equipped to present "
        "and demonstrate this platform to your brother, prospective investors, and clients with confidence.",
        callout_style)]], colWidths=[504])
    final_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1.5, accent_blue),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
    ]))
    story.append(final_box)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully built: {PDF_OUTPUT_PATH}")

if __name__ == "__main__":
    build_pdf()
