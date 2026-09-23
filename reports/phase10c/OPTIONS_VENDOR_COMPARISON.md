# Phase 10C: Options Vendor Comparison

## Question B Evaluation: Options Execution Data
Requirement: Can a legitimate provider supply genuine historical timestamp, underlying, expiry, strike, option_type, bid, ask (and order depth) to construct a continuous executable surface?

### Master Options Execution Comparison (Table 2)

| Provider | Historical Options | Bid | Ask | Paired Quotes | Continuous Surface | Expired Contracts | Order Book | Level | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| NSE Data & Analytics | >10 years full F&O contracts history with all strikes/expiries | VERIFIED | VERIFIED | VERIFIED_IN_RAW_SNAPSHOTS | RECONSTRUCTION_PIPELINE_REQUIRED | VERIFIED (Comprehensive historical archive of all expired contracts) | VERIFIED (Level 2: 5-depth snapshot; Level 3: full order book messages) | LEVEL_2_CAPABLE_LEVEL_3_UNRECONSTRUCTED | RECONSTRUCTION_REQUIRED_FOR_LEVEL_3 |
| TrueData | Multi-year 1m/5m OHLCV for expired F&O contracts | PROVIDER_CLAIM_UNVERIFIED | PROVIDER_CLAIM_UNVERIFIED | UNVERIFIED_HISTORICAL | UNVERIFIED | VERIFIED (Expired options OHLCV bars back to 2018+) | LIVE_ONLY_LEVEL_2 (Live feed has 5-depth; standard historical API serves OHLCV bars) | LEVEL_1 | COMMERCIAL_TICK_ARCHIVE_UNVERIFIED |
| GlobalDataFeeds / GDFL | Multi-year historical OHLCV for active and expired options | PROVIDER_CLAIM_UNVERIFIED | PROVIDER_CLAIM_UNVERIFIED | UNVERIFIED_HISTORICAL | UNVERIFIED | VERIFIED (Expired F&O contracts available in bar format) | LIVE_ONLY_LEVEL_2 (Live feed delivers 5-depth; historical is OHLCV) | LEVEL_1 | COMMERCIAL_TICK_ARCHIVE_UNVERIFIED |
| Zerodha Kite Connect | NOT_AVAILABLE (Expired options contracts are purged from instrument master upon expiry) | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE (Tokens purged post-expiry; not queryable in historical API) | LIVE_ONLY_LEVEL_2 (Live /quote API returns 5-depth; historical endpoint does not) | LEVEL_0 | INSUFFICIENT_HISTORICAL_BID_ASK |
| Upstox | NOT_AVAILABLE (Expired options contracts not retained in historical query endpoint) | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE | LIVE_ONLY_LEVEL_2 (Live market feed provides Best 5; historical endpoint provides OHLCV only) | LEVEL_0 | INSUFFICIENT_HISTORICAL_BID_ASK |
| Angel One SmartAPI | NOT_AVAILABLE (Expired F&O contracts not accessible via historical API) | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE | LIVE_ONLY_LEVEL_2 (Snapquote live endpoint provides Best 5; historical provides OHLCV only) | LEVEL_0 | INSUFFICIENT_HISTORICAL_BID_ASK |
| FYERS | NOT_AVAILABLE (Expired options contracts are pruned) | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE | LIVE_ONLY_LEVEL_2 (Live WebSocket has 5-depth; historical has none) | LEVEL_0 | INSUFFICIENT_HISTORICAL_BID_ASK |
| Yahoo Finance | NOT_AVAILABLE (Current snapshot chains only; zero historical expired chains) | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE | LEVEL_0 | INSUFFICIENT_HISTORICAL_OPTIONS |
| NSE Public Bhavcopy | VERIFIED (>10 years daily settlement, volume, OI for all expired contracts) | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE | VERIFIED (Full EOD history of expired contracts) | NOT_AVAILABLE | LEVEL_0 | EOD_SETTLEMENT_ONLY |

## Key Findings for Question B & Critical Distinctions

### Critical Broker Rule (Section 10)
Every broker was evaluated independently based strictly on its documented historical endpoints:
- **Zerodha Kite Connect**: Historical endpoint returns exclusively `[timestamp, open, high, low, close, volume, oi]`. Zero Bid/Ask.
- **Upstox**: Historical endpoint returns `[timestamp, open, high, low, close, volume, open_interest]`. Zero Bid/Ask.
- **Angel One SmartAPI**: Historical endpoint returns `[timestamp, open, high, low, close, volume]`. Zero Bid/Ask.
- **FYERS**: Historical endpoint returns `[timestamp, open, high, low, close, volume]`. Zero Bid/Ask.
- **Finding**: All retail broker historical endpoints provide ONLY LTP-derived OHLCV+OI candles. Furthermore, expired options contracts are purged from instrument masters. Brokers are classified as **INSUFFICIENT** for options execution research.

### Critical NSE Rule (Section 11)
- **NSE Data & Analytics** is the sole direct source containing historical Level 2 (5-depth) snapshots and Level 3 Tick-by-Tick (TBT) order messages for expired F&O contracts.
- Raw order messages and periodic snapshots do NOT constitute a ready-made continuous executable Bid/Ask time series out-of-the-box.
- Reconstructing a continuous Level 3/4 surface requires enterprise licensing, massive data ingestion (terabytes), and an order matching engine simulation pipeline.
- Therefore, NSE Data & Analytics is classified as **LEVEL_2_CAPABLE_LEVEL_3_UNRECONSTRUCTED** and requires an enterprise pipeline before it can be deemed research-ready.

### Commercial Redistributors (TrueData / GDFL)
- Live feeds support Level 1/Level 2 Best 5 market depth.
- Standard self-service historical APIs return OHLCV+OI bars (Level 1).
- Historical tick-level Bid/Ask archives require custom enterprise sales quotation and empirical audit before acceptance.
