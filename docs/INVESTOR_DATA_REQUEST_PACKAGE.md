# INVESTOR DATA ACQUISITION & VENDOR REQUEST PACKAGE
**Indian Options AI Platform — Commercial Data Request Specification**
*Release: 17.0.0-INVESTOR-FROZEN | Milestone: Phase 17A | Standard: Institutional Quantitative Procurement*

---

## 1. Overview & Data Procurement Objective

This document defines the formal technical request package for acquiring commercial market datasets for the National Stock Exchange of India (NSE). 

> [!IMPORTANT]
> **COMPLIANCE & TRUTH DIRECTIVE**
> - Vendor capabilities and pricing are never assumed.
> - Whenever a provider capability has not been independently verified via live test payloads, it is formally marked as **`REQUIRES_VENDOR_CONFIRMATION`**.
> - Automated purchasing remains locked (`PURCHASE_AUTHORIZED=FALSE`) until commercial terms are formally approved.

---

## 2. Formal Dataset Request Specifications

### Dataset 1: Historical Equity & Index Intraday Panel (1-Minute & 5-Minute Bars)
- **DATASET**: Multi-Year NSE Equity & Index Intraday Aggregates
- **EXACT FIELDS**: `[timestamp_ist, symbol, open, high, low, close, volume, vwap, trade_count]`
- **MINIMUM HISTORY**: 2 years (~500 sessions, ~187,500 1-min bars per symbol)
- **IDEAL HISTORY**: 5–10 years (2014–Present)
- **TIMESTAMP REQUIREMENTS**:
  - ISO-8601 with explicit IST offset (`YYYY-MM-DDTHH:MM:SS+05:30`).
  - Bar timestamps must represent **bar close** (e.g. 09:16:00 represents interval [09:15:00, 09:16:00]).
  - Zero missing minutes during official exchange trading hours (09:15:00 to 15:30:00 IST).
- **SOURCE CANDIDATES**:
  1. *TruData*: REST API & Bulk Parquet (NSE Authorized Vendor) — `REQUIRES_VENDOR_CONFIRMATION`
  2. *GlobalDataFeeds (GDFL)*: Historical Data Feed — `REQUIRES_VENDOR_CONFIRMATION`
  3. *Zerodha Kite Connect Historical API*: Retail broker API (1–2 years history available)
- **ACCOUNT REQUIREMENT**: Commercial vendor enterprise contract or funded retail broker account.
- **FREE/PAID STATUS**: Paid commercial subscription.
- **LICENSE REQUIREMENT**: Internal quantitative research and investor platform demonstration license. Commercial redistribution restricted.
- **SAMPLE REQUIRED**: 1 full calendar month (e.g. January 2024) of 1-minute bars for NIFTY 50 and BANK NIFTY.
- **CERTIFICATION TEST**:
  - Synthetic daily aggregation test: `sum(volume_1m) == bhavcopy_volume` and `high_1m == bhavcopy_high` to within $0.05\%$.
  - Continuity test: Zero missing trading-minute timestamps on regular exchange days.

---

### Dataset 2: Historical Index Options Chain with Paired Bid/Ask Quotes
- **DATASET**: High-Fidelity Historical Options Order-Book Quotes (NIFTY & BANKNIFTY)
- **EXACT FIELDS**: `[timestamp_ist, underlying_symbol, expiry_date, strike, option_type, ltp, bid_price, ask_price, bid_qty, ask_qty, volume, open_interest, change_in_oi]`
- **MINIMUM HISTORY**: 2 years of weekly expiry cycles
- **IDEAL HISTORY**: 5+ years (2019–Present)
- **TIMESTAMP REQUIREMENTS**:
  - Minimum 1-minute snapshot intervals; ideally tick-by-tick (TBT).
  - Exchange matching-engine timestamp preferred over vendor ingestion timestamp.
- **SOURCE CANDIDATES**:
  1. *TruData Historical Options Tick/Minute Store*: `REQUIRES_VENDOR_CONFIRMATION`
  2. *GlobalDataFeeds (GDFL) Historical Level 2/3 Store*: `REQUIRES_VENDOR_CONFIRMATION`
  3. *NSE Data & Analytics (DotEx)*: Direct exchange historical tick files — `REQUIRES_VENDOR_CONFIRMATION`
- **ACCOUNT REQUIREMENT**: Direct commercial vendor contract.
- **FREE/PAID STATUS**: Paid institutional feed (`SALES_QUOTE_REQUIRED`).
- **LICENSE REQUIREMENT**: Quantitative fund research, backtesting, and investor presentation rights.
- **SAMPLE REQUIRED**: 2 full weekly expiry cycles for NIFTY options across all strikes within $\pm 7.5\%$ of spot.
- **CERTIFICATION TEST**:
  - Authenticity test: `bid_price > 0` and `ask_price > 0` for $> 95\%$ of active strikes.
  - Zero crossed quotes: $\text{Bid} \le \text{Ask}$ for $100.0\%$ of observations.
  - Arbitrage bound verification: Option prices strictly adhere to intrinsic lower bounds.
  - Continuous executable surface coverage $\ge 90.0\%$ (vs current baseline of $0.0\%$).

---

### Dataset 3: Real-Time Level 2 Market Depth Feed (Best 5 Quotes)
- **DATASET**: Live Streaming Market Depth & Order Flow (Index & Options)
- **EXACT FIELDS**:
  - `[quote_timestamp, symbol, ltp, last_traded_qty, volume, oi]`
  - `best_5_bids`: Array of 5 `[bid_price, bid_qty, order_count]`
  - `best_5_asks`: Array of 5 `[ask_price, ask_qty, order_count]`
  - `[total_buy_qty, total_sell_qty]`
- **MINIMUM HISTORY**: Live streaming during market hours (09:15 to 15:30 IST)
- **IDEAL HISTORY**: Continuous real-time capture persisted to daily Parquet archives
- **TIMESTAMP REQUIREMENTS**:
  - Millisecond precision exchange timestamp ($T_{\text{exchange}}$).
  - Transit latency $(T_{\text{received}} - T_{\text{exchange}}) \le 250\text{ms}$.
- **SOURCE CANDIDATES**:
  1. *Zerodha Kite Connect WebSocket API (Full Mode)*: Operational stub ready.
  2. *Upstox Market Data Feed v2*: Operational stub ready.
  3. *Angel One SmartAPI WebSocket 2.0*: Integration stub implemented (`ANGELONE_STATUS = CREDENTIAL_UNCONFIGURED`).
  4. *TruData Real-Time WebSocket*: `REQUIRES_VENDOR_CONFIRMATION`.
- **ACCOUNT REQUIREMENT**: Active trading Demat account with API subscription enabled.
- **FREE/PAID STATUS**: Free to ₹4,000/month depending on broker platform.
- **LICENSE REQUIREMENT**: Internal non-redistributed algorithmic trading and paper simulation.
- **SAMPLE REQUIRED**: 1 live market session recording (09:15 to 15:30 IST) of Best-5 quotes.
- **CERTIFICATION TEST**:
  - Latency stress test: Sustained processing of $> 1,000$ packet updates per second without memory leakage.
  - Bid-Ask crossing fidelity: Verification that market orders fill strictly against prevailing Best-Ask (buys) or Best-Bid (sells).

---

### Dataset 4: Continuous Implied Volatility & Greeks Time-Series
- **DATASET**: Full EOD Implied Volatility Surface & Greeks Grid
- **EXACT FIELDS**: `[date, symbol, expiry, strike, option_type, underlying_price, iv, delta, gamma, theta_1d, vega_1pct, rho_1pct, pcr_oi, max_pain]`
- **MINIMUM HISTORY**: 5 years (2020–Present)
- **IDEAL HISTORY**: 10 years (2014–Present)
- **TIMESTAMP REQUIREMENTS**: End of Day (T+0 18:30 IST).
- **SOURCE CANDIDATES**:
  1. *Platform Internal Engine (Bhavcopy Parsed)*: Verified zero-cost source.
  2. *TruData Pre-Computed Greek Analytics*: `REQUIRES_VENDOR_CONFIRMATION`.
- **ACCOUNT REQUIREMENT**: None for Bhavcopy.
- **FREE/PAID STATUS**: Free (Internal Computation).
- **LICENSE REQUIREMENT**: Public regulatory data.
- **SAMPLE REQUIRED**: Complete current year surface.
- **CERTIFICATION TEST**:
  - Solver convergence: Newton-Raphson + Brent convergence rate $> 99.5\%$.
  - Greeks consistency: Numerical finite-difference derivative matches analytical formula to within $0.1\%$.

---

### Dataset 5: Timestamped Indian Macroeconomic & Financial Event Stream
- **DATASET**: RBI Monetary Policy, Macro Indicators, and Corporate Announcements
- **EXACT FIELDS**: `[event_id, event_type, published_timestamp_utc, effective_timestamp_ist, entity, headline, actual_value, forecast_value, previous_value, source_url]`
- **MINIMUM HISTORY**: 3 years
- **IDEAL HISTORY**: 10 years
- **TIMESTAMP REQUIREMENTS**: Exact microsecond/millisecond public release timestamp.
- **SOURCE CANDIDATES**:
  1. *Reserve Bank of India (DBIE & Official Press Releases)*: Public domain.
  2. *NSE Corporate Announcements Dissemination*: Official exchange XML/JSON feed.
  3. *Bloomberg / Refinitiv Event Feeds*: `REQUIRES_VENDOR_CONFIRMATION` (`SALES_QUOTE_REQUIRED`).
- **ACCOUNT REQUIREMENT**: None for RBI/NSE; institutional subscription for Bloomberg/Refinitiv.
- **FREE/PAID STATUS**: Free (RBI/NSE public) or Paid commercial.
- **LICENSE REQUIREMENT**: Public domain regulatory disclosures.
- **SAMPLE REQUIRED**: Last 12 RBI Monetary Policy Committee (MPC) announcement cycles.
- **CERTIFICATION TEST**:
  - Causality test: Signal generation timestamp strictly greater than announcement timestamp ($T_{\text{signal}} \ge T_{\text{announcement}} + \text{latency}$).
