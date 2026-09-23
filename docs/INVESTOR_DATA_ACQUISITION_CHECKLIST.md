# INVESTOR DATA ACQUISITION CHECKLIST & SPECIFICATION
**Indian Options AI Platform — External Data Dependency Specification**
*Date: September 2026 | Milestone: Investor Demo Hardening | Governance: Zero-Cost Policy Active*

---

## 1. Overview & Data Acquisition Principles

This checklist specifies the exact external dataset requirements necessary to transition the platform from its current **`RESEARCH_ONLY / LIMITED_DATA`** state to an institutional execution and production alpha research system.

> [!IMPORTANT]
> **GOVERNANCE MANDATE — ZERO VENDOR FABRICATION**
> - All vendor capabilities and licensing terms represent verified public API documentation or official exchange dissemination circulars.
> - Vendor pricing must NOT be fabricated. Where sales quotes or enterprise agreements are required, status is marked as `SALES_QUOTE_REQUIRED`.
> - Commercial contracts and automated data purchases remain strictly **`DISABLED`** under current platform governance (`PURCHASE_AUTHORIZED=FALSE`).

---

## 2. Exhaustive Data Acquisition Specifications

### 2.1 Multi-Year Underlying Intraday Time-Series (Cash & Futures)
- **Target Assets**: NIFTY 50, BANK NIFTY, FINNIFTY, NIFTY MIDCAP 50, and Top 20 liquid F&O equities.
- **Required Fields**: `[timestamp_ist, open, high, low, close, volume, vwap, trade_count]`
- **Bar Granularity**: 1-minute and 5-minute non-overlapping bars.
- **Minimum Acceptable History**: 2 years (~500 trading sessions, ~187,500 1-min bars per symbol).
- **Ideal History**: 5–10 years (2014–Present, covering major market stress events and regime shifts).
- **Source Candidates**:
  1. *Zerodha Kite Connect Historical Data API*: Authenticated retail API (~1–2 years 1-min history).
  2. *Upstox Historical API v2*: Authenticated retail API (~1–2 years 1-min history).
  3. *TruData (NSE Authorized)*: Enterprise REST API / WebSocket (10+ years historical 1-min bars).
  4. *GlobalDataFeeds (GDFL)*: Enterprise data feeds.
- **Account Requirement**: Broker trading account (retail) or commercial enterprise vendor agreement.
- **Free / Paid Status**: Paid (Broker subscription ~₹2,000/mo or commercial vendor ~₹3,500–₹8,000/mo).
- **License Considerations**: Retail broker APIs are licensed for personal/internal research; commercial investor platforms and funds require authorized vendor redistribution licenses.
- **Validation Procedure**:
  - Verification of continuous timestamps without missing trading-minute intervals (09:15 to 15:30 IST).
  - Outlier spike detection: $\max |R_{1m}| < 0.05$ unless exchange circuit breaker triggered.
  - Reconciliation of daily synthetic OHLCV aggregated from 1-min bars against official NSE Equity Bhavcopy ($< 0.01\%$ discrepancy allowed).

---

### 2.2 Historical Options Chain with Paired Executable Bid/Ask Quotes
- **Target Assets**: NIFTY & BANK NIFTY Weekly & Monthly Options (all strikes within $\pm 10\%$ of spot).
- **Required Fields**: `[timestamp_ist, underlying, expiry_date, strike, option_type, ltp, bid_price, ask_price, bid_qty, ask_qty, volume, open_interest, change_in_oi]`
- **Bar Granularity**: 1-minute snapshot or continuous tick stream.
- **Minimum Acceptable History**: 2 years of continuous weekly expiry cycles.
- **Ideal History**: 5+ years (2019–Present, covering post-COVID volatility spikes and SEBI lot size revisions).
- **Source Candidates**:
  1. *TruData Historical Options Tick/Minute Database*: Official NSE vendor.
  2. *GlobalDataFeeds (GDFL) Tick Data*: Official NSE vendor.
  3. *NSE Data & Analytics (DotEx)*: Exchange direct historical tick data files.
- **Account Requirement**: Formal commercial data subscription contract.
- **Free / Paid Status**: Paid (`SALES_QUOTE_REQUIRED` / typically ₹50,000 – ₹2,50,000 annually depending on tick vs bar level).
- **License Considerations**: Academic/research use vs commercial demonstration licensing. Commercial dissemination requires exchange vendor compliance.
- **Validation Procedure**:
  - **No Synthetic Quotes**: Confirmation that Bid and Ask are authentic exchange limit-order book observations.
  - **No Crossed Markets**: $\text{Bid} \le \text{Ask}$ for $100\%$ of records.
  - **Arbitrage Bounds**: $C \ge \max(0, S - K e^{-rT})$ and $P \ge \max(0, K e^{-rT} - S)$.
  - **Put-Call Parity**: Continuous surface sanity checks.

---

### 2.3 Live Real-Time Options Market Depth (Best 5 Quotes)
- **Target Assets**: Front-week and second-week NIFTY and BANKNIFTY active options contracts.
- **Required Fields**: `[quote_timestamp, symbol, strike, expiry, best_5_bids [price, qty, orders], best_5_asks [price, qty, orders], total_buy_qty, total_sell_qty, oi]`
- **Frequency**: Real-time streaming WebSocket (< 250ms tick dispatch).
- **Minimum Acceptable History**: Live streaming during active trading hours (09:15–15:30 IST).
- **Ideal History**: Continuous real-time stream logged to local Parquet/SQLite storage.
- **Source Candidates**:
  1. *Zerodha Kite Connect WebSocket (Full Mode)*: 5-depth order book for up to 3,000 instruments.
  2. *Upstox WebSocket Feed*: Live depth and market quote packets.
  3. *Angel One SmartAPI WebSocket 2.0*: Best-5 snapquote streaming.
  4. *Shoonya (Finvasia)*: Free API streaming WebSocket.
- **Account Requirement**: Active Demat/trading account with developer API access enabled.
- **Free / Paid Status**: Retail broker API costs (₹0 to ₹4,000/month).
- **License Considerations**: Retail programmatic personal trading and internal analytics; redistribution to third parties prohibited.
- **Validation Procedure**:
  - Timestamp latency check: $(T_{\text{received}} - T_{\text{provider}}) \le 300\text{ms}$.
  - Microstructure sanity: Cumulative bid depth vs ask depth calculation.
  - Connection resilience: Automated reconnection and missing sequence detection.

---

### 2.4 Historical Implied Volatility (IV) & Greeks Surface
- **Target Assets**: Full implied volatility surface across all strikes and expiries for NIFTY, BANKNIFTY.
- **Required Fields**: `[date, underlying_symbol, expiry_date, strike, option_type, underlying_price, iv, delta, gamma, theta_1d, vega_1pct, rho_1pct, pcr_oi, max_pain]`
- **Frequency**: End-of-Day (EOD) historical surface + Intraday 15-min surface.
- **Minimum Acceptable History**: 5 years of daily EOD surface data (2020–Present).
- **Ideal History**: 10 years (2014–Present).
- **Source Candidates**:
  1. *Computed via Platform Engine from NSE FO Bhavcopy*: Zero cost; official regulatory EOD archives.
  2. *TruData Volatility Database*: Pre-computed continuous Greek surfaces.
- **Account Requirement**: None for official Bhavcopy; vendor account for TruData.
- **Free / Paid Status**: Free (Platform Bhavcopy computation) or Paid commercial.
- **License Considerations**: Public regulatory dissemination (NSE Bhavcopy).
- **Validation Procedure**:
  - Solver convergence audit: Newton-Raphson + Brent convergence rate $> 99.5\%$ of liquid strikes.
  - Greeks unit scaling check: $\Theta$ per calendar day, $\nu$ per 1% vol, $\rho$ per 1% rate.
  - Monotonicity checks: IV smile curvature convexity ($\frac{\partial^2 \sigma_{\text{IV}}}{\partial K^2} > 0$ near ATM).

---

### 2.5 Timestamped News & Corporate Announcements
- **Target Assets**: Macro economic announcements (RBI MPC, CPI, GDP, Budget) and NIFTY 50 corporate news.
- **Required Fields**: `[article_id, title, published_timestamp_utc, received_timestamp_utc, source_domain, raw_content, entity_tags, materiality_rating]`
- **Frequency**: Event-driven streaming / continuous polling.
- **Minimum Acceptable History**: 2 years of timestamped financial news archive.
- **Ideal History**: 5+ years.
- **Source Candidates**:
  1. *RBI Official Dissemination (`rbi.org.in`)*: Monetary policy dates and policy rate announcements.
  2. *NSE Corporate Announcements Feed (`nseindia.com`)*: Official regulatory corporate disclosures.
  3. *Financial RSS Feeds (Moneycontrol, Economic Times)*: Polled news storage.
  4. *NewsAPI / Bloomberg / Refinitiv*: Commercial news feeds (`SALES_QUOTE_REQUIRED`).
- **Account Requirement**: None for public RSS/RBI/NSE; API key for commercial feeds.
- **Free / Paid Status**: Free for RSS/Public; Paid for commercial APIs.
- **License Considerations**: Web scraping subject to terms of service; RSS non-commercial use.
- **Validation Procedure**:
  - Temporal sequence enforcement: $T_{\text{published}} \le T_{\text{received}} \le T_{\text{processed}}$.
  - Elimination of look-ahead bias: Signal generated strictly on $T_{\text{processed}}$.

---

### 2.6 Macroeconomic Context & Volatility Benchmarks
- **Target Assets**: India VIX, RBI Repo Rate, TREPS / 91-Day T-Bill Yield, USDINR Exchange Rate.
- **Required Fields**: `[date, indicator_symbol, value, change, source_agency]`
- **Frequency**: Daily EOD.
- **Minimum Acceptable History**: 10 years (2014–Present).
- **Ideal History**: 15 years.
- **Source Candidates**:
  1. *NSE India VIX Archives (`archives.nseindia.com`)*: Daily historical India VIX.
  2. *Reserve Bank of India DBIE (`dbie.rbi.org.in`)*: Historical interest rates and MIBOR.
  3. *Yahoo Finance (`^INDIAVIX`, `INR=X`)*: Secondary validation stream.
- **Account Requirement**: None.
- **Free / Paid Status**: Free (Official Government & Regulatory Public Data).
- **License Considerations**: Public domain regulatory data.
- **Validation Procedure**:
  - Zero missing values on official trading days.
  - Risk-free rate mapping: $r(t)$ dynamically parameterized in Black-Scholes rather than static 6.5%.
