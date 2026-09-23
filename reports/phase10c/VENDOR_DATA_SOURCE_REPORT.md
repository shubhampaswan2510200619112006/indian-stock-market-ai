# Phase 10C: Vendor Data Source Report

## Executive Summary
This report provides an objective technical evaluation of 9 candidate data providers to resolve the project's data bottlenecks:
1. Multi-year high-resolution NIFTY 50 and BANKNIFTY intraday OHLCV (>= 250 sessions).
2. Genuine historical options Bid/Ask execution data (Level 3/4 continuous surface).

## Evaluated Providers & Verification Status

| Provider | Product | Access Method | Credentials | Pricing | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| NSE Data & Analytics | Historical Tick-by-Tick (TBT) & 5-Depth Snapshot Data | S3 Cloud Delivery / SFTP / External Media / API | CREDENTIAL_REQUIRED | SALES_QUOTE_REQUIRED | VERIFIED |
| TrueData | TrueData Historical REST API & Market Feeds | REST API / WebSocket / Python SDK | CREDENTIAL_REQUIRED | ₹2,000–₹4,000/month (Standard API); Tick F&O archives: SALES_QUOTE_REQUIRED | VERIFIED |
| GlobalDataFeeds / GDFL | GDFL Nimble / DataFeeds API | Desktop API (COM/DLL) / REST / WebSocket | CREDENTIAL_REQUIRED | SALES_QUOTE_REQUIRED (Retail live ~₹1,800/mo; historical bulk tick requires custom quote) | VERIFIED |
| Zerodha Kite Connect | Kite Connect Historical API v3 | REST API | CREDENTIAL_REQUIRED | ₹4,000/month (₹2,000 Kite Connect base API + ₹2,000 Historical add-on) | VERIFIED |
| Upstox | Upstox Developer API v2 Historical Candle Data | REST API | CREDENTIAL_REQUIRED | Free API access with active Upstox trading account | VERIFIED |
| Angel One SmartAPI | Angel One SmartAPI Historical Data | REST API | CREDENTIAL_REQUIRED | Free for retail algorithmic traders with trading account | VERIFIED |
| FYERS | FYERS API v3 Historical Data | REST API | CREDENTIAL_REQUIRED | Free for FYERS trading account holders | VERIFIED |
| Yahoo Finance | Yahoo Finance Chart API (yfinance) | Public HTTP API / yfinance | NO | Free | VERIFIED |
| NSE Public Bhavcopy | NSE Public All Reports / F&O Bhavcopy | Public Web Download / CSV Archives | NO | Free | VERIFIED |

## Detailed Provider Catalog Profiles

### NSE Data & Analytics
- **Product**: Historical Tick-by-Tick (TBT) & 5-Depth Snapshot Data
- **Official Documentation**: [https://www.nseindia.com/market-data/historical-data-products](https://www.nseindia.com/market-data/historical-data-products)
- **Verification Timestamp**: `2026-09-09T13:27:00Z`
- **Intraday History**: >10 years available across indices and equity segments
- **Options History**: >10 years full F&O contracts history with all strikes/expiries
- **Historical Bid/Ask**: LEVEL 2 / LEVEL 3 CAPABLE
- **Order Book Depth**: VERIFIED (Level 2: 5-depth snapshot; Level 3: full order book messages)
- **Expired Contracts**: VERIFIED (Comprehensive historical archive of all expired contracts)
- **Suitability Score**: **90 / 100**
- **Intraday Track**: `PASS`
- **Options Track**: `POTENTIAL_WITH_RECONSTRUCTION`
- **Notes**: Authoritative exchange direct source. Contains true historical Bid/Ask and order log data. Raw order-by-order requires specialized reconstruction pipeline to form continuous executable surfaces.

### TrueData
- **Product**: TrueData Historical REST API & Market Feeds
- **Official Documentation**: [https://www.truedata.in](https://www.truedata.in)
- **Verification Timestamp**: `2026-09-09T13:27:00Z`
- **Intraday History**: >10 years 1m and 5m continuous history for NIFTY 50 and BANKNIFTY
- **Options History**: Multi-year 1m/5m OHLCV for expired F&O contracts
- **Historical Bid/Ask**: LEVEL 1 (Standard REST API provides OHLCV+OI; historical tick Bid/Ask requires enterprise archive)
- **Order Book Depth**: LIVE_ONLY_LEVEL_2 (Live feed has 5-depth; standard historical API serves OHLCV bars)
- **Expired Contracts**: VERIFIED (Expired options OHLCV bars back to 2018+)
- **Suitability Score**: **76 / 100**
- **Intraday Track**: `PASS`
- **Options Track**: `BLOCKED_PENDING_ENTERPRISE_VERIFICATION`
- **Notes**: Best-in-class authorized vendor for multi-year NIFTY/BANKNIFTY 1m/5m OHLCV. Fully satisfies Question A (>250 sessions). Options historical Bid/Ask continuous surface not available on standard retail tier.

### GlobalDataFeeds / GDFL
- **Product**: GDFL Nimble / DataFeeds API
- **Official Documentation**: [https://www.globaldatafeeds.in](https://www.globaldatafeeds.in)
- **Verification Timestamp**: `2026-09-09T13:27:00Z`
- **Intraday History**: >5 years 1m and 5m intraday OHLCV for indices and futures
- **Options History**: Multi-year historical OHLCV for active and expired options
- **Historical Bid/Ask**: LEVEL 1 (Standard historical feed delivers OHLCV bars; continuous Bid/Ask unverified)
- **Order Book Depth**: LIVE_ONLY_LEVEL_2 (Live feed delivers 5-depth; historical is OHLCV)
- **Expired Contracts**: VERIFIED (Expired F&O contracts available in bar format)
- **Suitability Score**: **75 / 100**
- **Intraday Track**: `PASS`
- **Options Track**: `BLOCKED_PENDING_ENTERPRISE_VERIFICATION`
- **Notes**: Authorized NSE vendor. Fully satisfies Question A (1m/5m intraday >250 sessions). Historical options Bid/Ask continuous surface not verified on standard endpoints.

### Zerodha Kite Connect
- **Product**: Kite Connect Historical API v3
- **Official Documentation**: [https://kite.trade/docs/connect/v3/historical/](https://kite.trade/docs/connect/v3/historical/)
- **Verification Timestamp**: `2026-09-09T13:27:00Z`
- **Intraday History**: >1-2 years 1m/5m chunked historical OHLCV for active indices
- **Options History**: NOT_AVAILABLE (Expired options contracts are purged from instrument master upon expiry)
- **Historical Bid/Ask**: NOT_AVAILABLE (Historical API endpoint returns exclusively [timestamp, open, high, low, close, volume, oi])
- **Order Book Depth**: LIVE_ONLY_LEVEL_2 (Live /quote API returns 5-depth; historical endpoint does not)
- **Expired Contracts**: NOT_AVAILABLE (Tokens purged post-expiry; not queryable in historical API)
- **Suitability Score**: **45 / 100**
- **Intraday Track**: `PASS`
- **Options Track**: `BLOCKED`
- **Notes**: Verified against official API docs. Documented historical endpoint provides strictly OHLCV+OI derived from LTP. Zero historical Bid/Ask. Zero expired options contracts. INSUFFICIENT for options execution.

### Upstox
- **Product**: Upstox Developer API v2 Historical Candle Data
- **Official Documentation**: [https://upstox.com/developer/api-documentation/historical-candle-data](https://upstox.com/developer/api-documentation/historical-candle-data)
- **Verification Timestamp**: `2026-09-09T13:27:00Z`
- **Intraday History**: ~1-2 years 1m/5m OHLCV for cash and active index contracts
- **Options History**: NOT_AVAILABLE (Expired options contracts not retained in historical query endpoint)
- **Historical Bid/Ask**: NOT_AVAILABLE (Documented response format: [timestamp, open, high, low, close, volume, open_interest])
- **Order Book Depth**: LIVE_ONLY_LEVEL_2 (Live market feed provides Best 5; historical endpoint provides OHLCV only)
- **Expired Contracts**: NOT_AVAILABLE
- **Suitability Score**: **47 / 100**
- **Intraday Track**: `PASS`
- **Options Track**: `BLOCKED`
- **Notes**: Verified against official documentation. Historical endpoints serve strictly LTP-based OHLCV candles. Zero historical Bid/Ask. INSUFFICIENT for options execution.

### Angel One SmartAPI
- **Product**: Angel One SmartAPI Historical Data
- **Official Documentation**: [https://smartapi.angelbroking.com/docs/Historical](https://smartapi.angelbroking.com/docs/Historical)
- **Verification Timestamp**: `2026-09-09T13:27:00Z`
- **Intraday History**: ~1 year 1m, multi-year daily for active symbols
- **Options History**: NOT_AVAILABLE (Expired F&O contracts not accessible via historical API)
- **Historical Bid/Ask**: NOT_AVAILABLE (Documented response format: [timestamp, open, high, low, close, volume])
- **Order Book Depth**: LIVE_ONLY_LEVEL_2 (Snapquote live endpoint provides Best 5; historical provides OHLCV only)
- **Expired Contracts**: NOT_AVAILABLE
- **Suitability Score**: **47 / 100**
- **Intraday Track**: `PASS`
- **Options Track**: `BLOCKED`
- **Notes**: Verified against official documentation. Historical endpoint provides strictly OHLCV bars. Zero historical Bid/Ask. INSUFFICIENT for options execution.

### FYERS
- **Product**: FYERS API v3 Historical Data
- **Official Documentation**: [https://myapi.fyers.in/docs/](https://myapi.fyers.in/docs/)
- **Verification Timestamp**: `2026-09-09T13:27:00Z`
- **Intraday History**: ~100 days 1m chunked, 1-2 years 5m for active symbols
- **Options History**: NOT_AVAILABLE (Expired options contracts are pruned)
- **Historical Bid/Ask**: NOT_AVAILABLE (Candle array contains [timestamp, open, high, low, close, volume])
- **Order Book Depth**: LIVE_ONLY_LEVEL_2 (Live WebSocket has 5-depth; historical has none)
- **Expired Contracts**: NOT_AVAILABLE
- **Suitability Score**: **43 / 100**
- **Intraday Track**: `PASS`
- **Options Track**: `BLOCKED`
- **Notes**: Verified against official API docs. Strictly LTP-derived OHLCV candles. Zero historical Bid/Ask. INSUFFICIENT for options execution.

### Yahoo Finance
- **Product**: Yahoo Finance Chart API (yfinance)
- **Official Documentation**: [https://finance.yahoo.com](https://finance.yahoo.com)
- **Verification Timestamp**: `2026-09-09T13:27:00Z`
- **Intraday History**: 7 sessions (1m), 59 sessions (5m); 1h auxiliary reaches 724 sessions but cannot substitute for 1m/5m
- **Options History**: NOT_AVAILABLE (Current snapshot chains only; zero historical expired chains)
- **Historical Bid/Ask**: NOT_AVAILABLE
- **Order Book Depth**: NOT_AVAILABLE
- **Expired Contracts**: NOT_AVAILABLE
- **Suitability Score**: **25 / 100**
- **Intraday Track**: `BLOCKED`
- **Options Track**: `BLOCKED`
- **Notes**: Empirically audited baseline. Fails 250-session threshold for 1m and 5m. Zero historical options Bid/Ask. INSUFFICIENT for both Intraday and Options research.

### NSE Public Bhavcopy
- **Product**: NSE Public All Reports / F&O Bhavcopy
- **Official Documentation**: [https://www.nseindia.com/all-reports](https://www.nseindia.com/all-reports)
- **Verification Timestamp**: `2026-09-09T13:27:00Z`
- **Intraday History**: NOT_AVAILABLE (EOD daily settlement files only)
- **Options History**: VERIFIED (>10 years daily settlement, volume, OI for all expired contracts)
- **Historical Bid/Ask**: NOT_AVAILABLE (Bhavcopy reports Open, High, Low, Close, SettlePrice, Volume, OI; no bid/ask)
- **Order Book Depth**: NOT_AVAILABLE
- **Expired Contracts**: VERIFIED (Full EOD history of expired contracts)
- **Suitability Score**: **36 / 100**
- **Intraday Track**: `BLOCKED`
- **Options Track**: `BLOCKED`
- **Notes**: Excellent official baseline for daily EOD settlement and OI. Completely lacks intraday 1m/5m bars and historical Bid/Ask. INSUFFICIENT for Intraday and Options execution research.
