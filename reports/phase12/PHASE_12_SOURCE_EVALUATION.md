# Phase 12 — Market Data Source Evaluation

## 1. Candidate Source Comparison
| Source | Tier | Intraday 1m/5m | Options Bid/Ask | Pricing Status | Overall Suitability |
|---|---|---|---|---|---|
| **NSE Data & Analytics Ltd (DotEx)** | `OFFICIAL_EXCHANGE` | `SUITABLE_UPON_CONTRACT` | `UNSUITABLE` | `REQUIRES_VENDOR_QUOTE` | `ACQUISITION_CANDIDATE_PRIMARY` |
| **TrueData (TrueData India / Authorized NSE Vendor)** | `AUTHORIZED_VENDOR` | `UNSUITABLE_OR_LIMITED` | `UNSUITABLE` | `ESTIMATE` | `ACQUISITION_CANDIDATE_SECONDARY` |
| **Global DataFeeds (GDFL)** | `AUTHORIZED_VENDOR` | `SUITABLE_UPON_CONTRACT` | `UNSUITABLE` | `ESTIMATE` | `ACQUISITION_CANDIDATE_TERTIARY` |
| **Retail Broker APIs (Zerodha Kite Connect / Upstox / Angel One)** | `BROKER_API` | `UNSUITABLE_OR_LIMITED` | `UNSUITABLE` | `VERIFIED_QUOTE` | `INSUFFICIENT_FOR_OPTIONS_EXECUTION` |
| **Public / Free Endpoints (Yahoo Finance / NSE Public Web)** | `PUBLIC_FREE` | `UNSUITABLE_OR_LIMITED` | `UNSUITABLE` | `VERIFIED_QUOTE` | `INSUFFICIENT_FOR_INTRADAY_AND_OPTIONS` |

## 2. In-Depth Evaluation Across 18 Criteria

### NSE Data & Analytics Ltd (DotEx) — Historical Tick, 1-Min Snapshot, and Bhavcopy Archives
- **Tier**: `OFFICIAL_EXCHANGE`
- **Historical Depth**: VERIFIED (Multi-year, 5-10+ years available upon contract) | VERIFIED (Historical trade & order books by contract year)
- **Bid/Ask Quotes**: Historical Bid: `VERIFIED (Level 2 / 5-depth snapshot archives)`, Ask: `VERIFIED (Level 2 / 5-depth snapshot archives)`
- **Market Depth**: `{'level_1': 'VERIFIED', 'level_2_depth_5': 'VERIFIED (Available in historical depth products)', 'full_order_book': 'REQUIRES_VENDOR_CONFIRMATION (Available for institutional researchers upon specialized enterprise contract)'}`
- **Timestamp Precision**: `VERIFIED (Microsecond / Millisecond exchange matching timestamps)`, Timezone: `VERIFIED (Asia/Kolkata, UTC+05:30)`
- **Pricing**: Status: `REQUIRES_VENDOR_QUOTE`, Details: `{'historical_segment_pricing': 'Requires formal enterprise enquiry with NSE Data & Analytics commercial sales', 'estimated_annual_cost_inr': 'ESTIMATE (Typically INR 50,000 to INR 250,000+ depending on segment count and years)', 'status_note': 'No price may be purchased or contracted without explicit human review and authorization'}`

### TrueData (TrueData India / Authorized NSE Vendor) — TrueData Historical REST & WebSocket API / Velocity
- **Tier**: `AUTHORIZED_VENDOR`
- **Historical Depth**: N/A | N/A
- **Bid/Ask Quotes**: Historical Bid: `REQUIRES_VENDOR_CONFIRMATION (Historical 1m bar OHLCV verified; historical timestamped Bid/Ask quote surface requires options tick add-on)`, Ask: `REQUIRES_VENDOR_CONFIRMATION (Requires confirmation of historical spread depth)`
- **Market Depth**: `{'level_1_realtime': 'VERIFIED', 'historical_depth': 'REQUIRES_VENDOR_CONFIRMATION (Typically limited to top bid/ask or 5-depth in live stream)'}`
- **Timestamp Precision**: `VERIFIED (1-second / millisecond timestamping in API)`, Timezone: `VERIFIED (Asia/Kolkata, UTC+05:30)`
- **Pricing**: Status: `ESTIMATE`, Details: `{'estimated_annual_cost_inr': 'ESTIMATE (INR 25,000 to INR 60,000 per year for combined multi-year historical + API access)', 'quote_verification_date': '2026-09-09', 'quote_status': 'Requires current plan verification from TrueData portal before purchase'}`
- **Observed Limitations**:
  - `{'verification_date': '2026-09-09', 'limitation': 'Historical options Bid/Ask continuous quote surface requires dedicated historical tick/quote subscription; standard API provides 1m bar summaries.'}`

### Global DataFeeds (GDFL) — NimbleDataPro / DataFeed API
- **Tier**: `AUTHORIZED_VENDOR`
- **Historical Depth**: VERIFIED (Multi-year 1m/5m historical cache) | N/A
- **Bid/Ask Quotes**: Historical Bid: `REQUIRES_VENDOR_CONFIRMATION`, Ask: `REQUIRES_VENDOR_CONFIRMATION`
- **Market Depth**: `{'live_depth': 'VERIFIED (5-depth)', 'historical_depth': 'REQUIRES_VENDOR_CONFIRMATION'}`
- **Timestamp Precision**: `VERIFIED (1-second / bar timestamping)`, Timezone: `VERIFIED (Asia/Kolkata)`
- **Pricing**: Status: `ESTIMATE`, Details: `{'estimated_annual_cost_inr': 'ESTIMATE (INR 20,000 to INR 50,000 per year depending on segments)', 'status_note': 'Requires vendor quote confirmation prior to purchase'}`

### Retail Broker APIs (Zerodha Kite Connect / Upstox / Angel One) — Historical Data API Addon
- **Tier**: `BROKER_API`
- **Historical Depth**: VERIFIED (Up to 1-3 years via chunked REST calls) | N/A
- **Bid/Ask Quotes**: Historical Bid: `NOT_AVAILABLE (Broker historical APIs return ONLY OHLCV bars, never historical Bid/Ask quotes)`, Ask: `NOT_AVAILABLE`
- **Market Depth**: `{'historical_depth': 'NOT_AVAILABLE (Zero historical market depth archive)'}`
- **Timestamp Precision**: `VERIFIED (Minute bar timestamps)`, Timezone: `VERIFIED (Asia/Kolkata)`
- **Pricing**: Status: `VERIFIED_QUOTE`, Details: `{'monthly_cost_inr': 2000, 'annual_cost_inr': 24000, 'quote_type': 'VERIFIED_QUOTE (Kite Connect INR 2,000/month Base + Historical)'}`
- **Observed Limitations**:
  - `{'verification_date': '2026-09-09', 'limitation_type': 'OBSERVED_PROVIDER_LIMITATION', 'scope': 'OPTIONS_HISTORICAL_QUOTES', 'reason': 'Retail broker APIs strictly provide OHLCV bars for active tokens only; historical options Bid/Ask quotes and expired contracts are completely unavailable.'}`

### Public / Free Endpoints (Yahoo Finance / NSE Public Web) — Public Scraping / yfinance Free API
- **Tier**: `PUBLIC_FREE`
- **Historical Depth**: N/A | N/A
- **Bid/Ask Quotes**: Historical Bid: `None`, Ask: `None`
- **Market Depth**: `{'depth': 'NOT_AVAILABLE'}`
- **Timestamp Precision**: `VERIFIED (Minute timestamps when available)`, Timezone: `VERIFIED (Asia/Kolkata)`
- **Pricing**: Status: `VERIFIED_QUOTE`, Details: `{'annual_cost_inr': 0, 'quote_type': 'VERIFIED_QUOTE (Free public endpoint)'}`
- **Observed Limitations**:
  - `{'verification_date': '2026-09-09', 'limitation_type': 'OBSERVED_PROVIDER_LIMITATION', 'scope': 'INTRADAY_RETENTION_AND_OPTIONS', 'reason': 'Empirically verified in Phase 10A/10B: Yahoo Finance public 1m endpoint retains only ~7 calendar days and 5m endpoint retains only ~60 calendar days. Options quotes are entirely absent.'}`

