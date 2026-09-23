# Phase 10C: Intraday Vendor Comparison

## Question A Evaluation: Intraday Historical Coverage
Requirement: Can a legitimate provider supply NIFTY 50 and BANKNIFTY 1-minute and 5-minute historical OHLCV for >= 250 trading sessions (preferred >= 500 sessions / 2 years)?

### Master Vendor Comparison (Table 1)

| Provider | Product | NIFTY 1m | BANKNIFTY 1m | NIFTY 5m | BANKNIFTY 5m | Historical Options Bid/Ask | Options Level | Verification | Cost | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| NSE Data & Analytics | Historical Tick-by-Tick (TBT) & 5-Depth Snapshot Data | VERIFIED | VERIFIED | VERIFIED | VERIFIED | LEVEL 2 / LEVEL 3 CAPABLE | LEVEL_2_CAPABLE_LEVEL_3_UNRECONSTRUCTED | VERIFIED | SALES_QUOTE_REQUIRED | SUITABLE_FOR_INTRADAY |
| TrueData | TrueData Historical REST API & Market Feeds | VERIFIED | VERIFIED | VERIFIED | VERIFIED | LEVEL 1 (Standard REST API provides OHLCV+OI; historical tick Bid/Ask requires enterprise archive) | LEVEL_1 | VERIFIED | ₹2,000–₹4,000/month (Standard API); Tick F&O archives: SALES_QUOTE_REQUIRED | SUITABLE_FOR_INTRADAY |
| GlobalDataFeeds / GDFL | GDFL Nimble / DataFeeds API | VERIFIED | VERIFIED | VERIFIED | VERIFIED | LEVEL 1 (Standard historical feed delivers OHLCV bars; continuous Bid/Ask unverified) | LEVEL_1 | VERIFIED | SALES_QUOTE_REQUIRED (Retail live ~₹1,800/mo; historical bulk tick requires custom quote) | SUITABLE_FOR_INTRADAY |
| Zerodha Kite Connect | Kite Connect Historical API v3 | VERIFIED | VERIFIED | VERIFIED | VERIFIED | NOT_AVAILABLE (Historical API endpoint returns exclusively [timestamp, open, high, low, close, volume, oi]) | LEVEL_0 | VERIFIED | ₹4,000/month (₹2,000 Kite Connect base API + ₹2,000 Historical add-on) | SUITABLE_FOR_INTRADAY |
| Upstox | Upstox Developer API v2 Historical Candle Data | VERIFIED | VERIFIED | VERIFIED | VERIFIED | NOT_AVAILABLE (Documented response format: [timestamp, open, high, low, close, volume, open_interest]) | LEVEL_0 | VERIFIED | Free API access with active Upstox trading account | SUITABLE_FOR_INTRADAY |
| Angel One SmartAPI | Angel One SmartAPI Historical Data | VERIFIED | VERIFIED | VERIFIED | VERIFIED | NOT_AVAILABLE (Documented response format: [timestamp, open, high, low, close, volume]) | LEVEL_0 | VERIFIED | Free for retail algorithmic traders with trading account | SUITABLE_FOR_INTRADAY |
| FYERS | FYERS API v3 Historical Data | VERIFIED | VERIFIED | VERIFIED | VERIFIED | NOT_AVAILABLE (Candle array contains [timestamp, open, high, low, close, volume]) | LEVEL_0 | VERIFIED | Free for FYERS trading account holders | SUITABLE_FOR_INTRADAY |
| Yahoo Finance | Yahoo Finance Chart API (yfinance) | NOT_AVAILABLE (Limited to 7 days = 7 sessions, below 250 threshold) | NOT_AVAILABLE (Limited to 7 days = 7 sessions, below 250 threshold) | NOT_AVAILABLE (Limited to 60 days = 59 sessions, below 250 threshold) | NOT_AVAILABLE (Limited to 60 days = 59 sessions, below 250 threshold) | NOT_AVAILABLE | LEVEL_0 | VERIFIED | Free | BLOCKED_FOR_INTRADAY |
| NSE Public Bhavcopy | NSE Public All Reports / F&O Bhavcopy | NOT_AVAILABLE (EOD only) | NOT_AVAILABLE (EOD only) | NOT_AVAILABLE (EOD only) | NOT_AVAILABLE (EOD only) | NOT_AVAILABLE (Bhavcopy reports Open, High, Low, Close, SettlePrice, Volume, OI; no bid/ask) | LEVEL_0 | VERIFIED | Free | BLOCKED_FOR_INTRADAY |

## Key Findings for Question A
1. **Commercial Vendors Meet and Exceed Project Threshold**: TrueData, GlobalDataFeeds (GDFL), and NSE Data & Analytics provide >5–10 years of 1m/5m intraday OHLCV (>1,250 to 2,500+ sessions), easily exceeding the 250-session threshold.
2. **Brokers Supply Moderate Multi-Session History**: Zerodha Kite Connect, Upstox, and Angel One provide 1–2 years of 1m/5m historical candle data (250–500 sessions) for active index symbols via authenticated API endpoints.
3. **Free Baselines Fail Question A**: Yahoo Finance provides only 7 sessions for 1m and 59 sessions for 5m. NSE Public Bhavcopy provides only EOD settlement prices. Neither satisfies the 250-session threshold.
4. **Best Verified Intraday Source**: **TrueData / TrueData Historical REST API** provides the most practical, well-documented, and robust continuous multi-year 1m and 5m OHLCV time series.
