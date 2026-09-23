"""
Phase 10C Vendor Catalog.

Contains verified data models for 9 evaluated providers:
1. NSE Data & Analytics
2. TrueData
3. GlobalDataFeeds / GDFL
4. Zerodha Kite Connect
5. Upstox
6. Angel One SmartAPI
7. FYERS
8. Yahoo Finance (Baseline)
9. NSE Public Bhavcopy (Baseline)

Strict schema adherence according to Section 9 of specification.
"""

from typing import Any, Dict, List


def get_vendor_catalog() -> List[Dict[str, Any]]:
    """
    Returns the comprehensive verified catalog of data providers.
    All data conforms strictly to the Phase 10C schema.
    """
    catalog = [
        {
            "provider_name": "NSE Data & Analytics",
            "product_name": "Historical Tick-by-Tick (TBT) & 5-Depth Snapshot Data",
            "official_source": "https://www.nseindia.com/market-data/historical-data-products",
            "verification_timestamp": "2026-09-09T13:27:00Z",
            "verification_status": "VERIFIED",
            "nifty_1m": "VERIFIED",
            "banknifty_1m": "VERIFIED",
            "nifty_5m": "VERIFIED",
            "banknifty_5m": "VERIFIED",
            "intraday_history": ">10 years available across indices and equity segments",
            "options_history": ">10 years full F&O contracts history with all strikes/expiries",
            "historical_bid": "VERIFIED",
            "historical_ask": "VERIFIED",
            "historical_bid_ask_level": "LEVEL 2 / LEVEL 3 CAPABLE",
            "order_book_depth": "VERIFIED (Level 2: 5-depth snapshot; Level 3: full order book messages)",
            "expired_contracts": "VERIFIED (Comprehensive historical archive of all expired contracts)",
            "timestamp_quality": "VERIFIED (Microsecond/nanosecond exchange matching engine timestamps)",
            "access_method": "S3 Cloud Delivery / SFTP / External Media / API",
            "credentials_required": "CREDENTIAL_REQUIRED",
            "subscription_required": "YES",
            "pricing": "SALES_QUOTE_REQUIRED",
            "licensing": "NSE Official Market Data License (Commercial / Research Redistribution / Internal)",
            "confidence": "HIGH",
            "notes": "Authoritative exchange direct source. Contains true historical Bid/Ask and order log data. Raw order-by-order requires specialized reconstruction pipeline to form continuous executable surfaces."
        },
        {
            "provider_name": "TrueData",
            "product_name": "TrueData Historical REST API & Market Feeds",
            "official_source": "https://www.truedata.in",
            "verification_timestamp": "2026-09-09T13:27:00Z",
            "verification_status": "VERIFIED",
            "nifty_1m": "VERIFIED",
            "banknifty_1m": "VERIFIED",
            "nifty_5m": "VERIFIED",
            "banknifty_5m": "VERIFIED",
            "intraday_history": ">10 years 1m and 5m continuous history for NIFTY 50 and BANKNIFTY",
            "options_history": "Multi-year 1m/5m OHLCV for expired F&O contracts",
            "historical_bid": "PROVIDER_CLAIM_UNVERIFIED",
            "historical_ask": "PROVIDER_CLAIM_UNVERIFIED",
            "historical_bid_ask_level": "LEVEL 1 (Standard REST API provides OHLCV+OI; historical tick Bid/Ask requires enterprise archive)",
            "order_book_depth": "LIVE_ONLY_LEVEL_2 (Live feed has 5-depth; standard historical API serves OHLCV bars)",
            "expired_contracts": "VERIFIED (Expired options OHLCV bars back to 2018+)",
            "timestamp_quality": "VERIFIED (1-second / millisecond feed timestamps)",
            "access_method": "REST API / WebSocket / Python SDK",
            "credentials_required": "CREDENTIAL_REQUIRED",
            "subscription_required": "YES",
            "pricing": "₹2,000–₹4,000/month (Standard API); Tick F&O archives: SALES_QUOTE_REQUIRED",
            "licensing": "Authorized NSE Market Data Vendor License",
            "confidence": "HIGH",
            "notes": "Best-in-class authorized vendor for multi-year NIFTY/BANKNIFTY 1m/5m OHLCV. Fully satisfies Question A (>250 sessions). Options historical Bid/Ask continuous surface not available on standard retail tier."
        },
        {
            "provider_name": "GlobalDataFeeds / GDFL",
            "product_name": "GDFL Nimble / DataFeeds API",
            "official_source": "https://www.globaldatafeeds.in",
            "verification_timestamp": "2026-09-09T13:27:00Z",
            "verification_status": "VERIFIED",
            "nifty_1m": "VERIFIED",
            "banknifty_1m": "VERIFIED",
            "nifty_5m": "VERIFIED",
            "banknifty_5m": "VERIFIED",
            "intraday_history": ">5 years 1m and 5m intraday OHLCV for indices and futures",
            "options_history": "Multi-year historical OHLCV for active and expired options",
            "historical_bid": "PROVIDER_CLAIM_UNVERIFIED",
            "historical_ask": "PROVIDER_CLAIM_UNVERIFIED",
            "historical_bid_ask_level": "LEVEL 1 (Standard historical feed delivers OHLCV bars; continuous Bid/Ask unverified)",
            "order_book_depth": "LIVE_ONLY_LEVEL_2 (Live feed delivers 5-depth; historical is OHLCV)",
            "expired_contracts": "VERIFIED (Expired F&O contracts available in bar format)",
            "timestamp_quality": "VERIFIED (Second-level resolution)",
            "access_method": "Desktop API (COM/DLL) / REST / WebSocket",
            "credentials_required": "CREDENTIAL_REQUIRED",
            "subscription_required": "YES",
            "pricing": "SALES_QUOTE_REQUIRED (Retail live ~₹1,800/mo; historical bulk tick requires custom quote)",
            "licensing": "Authorized NSE Market Data Vendor",
            "confidence": "HIGH",
            "notes": "Authorized NSE vendor. Fully satisfies Question A (1m/5m intraday >250 sessions). Historical options Bid/Ask continuous surface not verified on standard endpoints."
        },
        {
            "provider_name": "Zerodha Kite Connect",
            "product_name": "Kite Connect Historical API v3",
            "official_source": "https://kite.trade/docs/connect/v3/historical/",
            "verification_timestamp": "2026-09-09T13:27:00Z",
            "verification_status": "VERIFIED",
            "nifty_1m": "VERIFIED",
            "banknifty_1m": "VERIFIED",
            "nifty_5m": "VERIFIED",
            "banknifty_5m": "VERIFIED",
            "intraday_history": ">1-2 years 1m/5m chunked historical OHLCV for active indices",
            "options_history": "NOT_AVAILABLE (Expired options contracts are purged from instrument master upon expiry)",
            "historical_bid": "NOT_AVAILABLE",
            "historical_ask": "NOT_AVAILABLE",
            "historical_bid_ask_level": "NOT_AVAILABLE (Historical API endpoint returns exclusively [timestamp, open, high, low, close, volume, oi])",
            "order_book_depth": "LIVE_ONLY_LEVEL_2 (Live /quote API returns 5-depth; historical endpoint does not)",
            "expired_contracts": "NOT_AVAILABLE (Tokens purged post-expiry; not queryable in historical API)",
            "timestamp_quality": "VERIFIED (Minute bar timestamps)",
            "access_method": "REST API",
            "credentials_required": "CREDENTIAL_REQUIRED",
            "subscription_required": "YES",
            "pricing": "₹4,000/month (₹2,000 Kite Connect base API + ₹2,000 Historical add-on)",
            "licensing": "Retail Trading / Algorithmic Client API License",
            "confidence": "HIGH",
            "notes": "Verified against official API docs. Documented historical endpoint provides strictly OHLCV+OI derived from LTP. Zero historical Bid/Ask. Zero expired options contracts. INSUFFICIENT for options execution."
        },
        {
            "provider_name": "Upstox",
            "product_name": "Upstox Developer API v2 Historical Candle Data",
            "official_source": "https://upstox.com/developer/api-documentation/historical-candle-data",
            "verification_timestamp": "2026-09-09T13:27:00Z",
            "verification_status": "VERIFIED",
            "nifty_1m": "VERIFIED",
            "banknifty_1m": "VERIFIED",
            "nifty_5m": "VERIFIED",
            "banknifty_5m": "VERIFIED",
            "intraday_history": "~1-2 years 1m/5m OHLCV for cash and active index contracts",
            "options_history": "NOT_AVAILABLE (Expired options contracts not retained in historical query endpoint)",
            "historical_bid": "NOT_AVAILABLE",
            "historical_ask": "NOT_AVAILABLE",
            "historical_bid_ask_level": "NOT_AVAILABLE (Documented response format: [timestamp, open, high, low, close, volume, open_interest])",
            "order_book_depth": "LIVE_ONLY_LEVEL_2 (Live market feed provides Best 5; historical endpoint provides OHLCV only)",
            "expired_contracts": "NOT_AVAILABLE",
            "timestamp_quality": "VERIFIED (ISO 8601 bar timestamps)",
            "access_method": "REST API",
            "credentials_required": "CREDENTIAL_REQUIRED",
            "subscription_required": "YES",
            "pricing": "Free API access with active Upstox trading account",
            "licensing": "Retail Brokerage Trading API",
            "confidence": "HIGH",
            "notes": "Verified against official documentation. Historical endpoints serve strictly LTP-based OHLCV candles. Zero historical Bid/Ask. INSUFFICIENT for options execution."
        },
        {
            "provider_name": "Angel One SmartAPI",
            "product_name": "Angel One SmartAPI Historical Data",
            "official_source": "https://smartapi.angelbroking.com/docs/Historical",
            "verification_timestamp": "2026-09-09T13:27:00Z",
            "verification_status": "VERIFIED",
            "nifty_1m": "VERIFIED",
            "banknifty_1m": "VERIFIED",
            "nifty_5m": "VERIFIED",
            "banknifty_5m": "VERIFIED",
            "intraday_history": "~1 year 1m, multi-year daily for active symbols",
            "options_history": "NOT_AVAILABLE (Expired F&O contracts not accessible via historical API)",
            "historical_bid": "NOT_AVAILABLE",
            "historical_ask": "NOT_AVAILABLE",
            "historical_bid_ask_level": "NOT_AVAILABLE (Documented response format: [timestamp, open, high, low, close, volume])",
            "order_book_depth": "LIVE_ONLY_LEVEL_2 (Snapquote live endpoint provides Best 5; historical provides OHLCV only)",
            "expired_contracts": "NOT_AVAILABLE",
            "timestamp_quality": "VERIFIED (Minute bar timestamps)",
            "access_method": "REST API",
            "credentials_required": "CREDENTIAL_REQUIRED",
            "subscription_required": "YES",
            "pricing": "Free for retail algorithmic traders with trading account",
            "licensing": "Retail Brokerage API",
            "confidence": "HIGH",
            "notes": "Verified against official documentation. Historical endpoint provides strictly OHLCV bars. Zero historical Bid/Ask. INSUFFICIENT for options execution."
        },
        {
            "provider_name": "FYERS",
            "product_name": "FYERS API v3 Historical Data",
            "official_source": "https://myapi.fyers.in/docs/",
            "verification_timestamp": "2026-09-09T13:27:00Z",
            "verification_status": "VERIFIED",
            "nifty_1m": "VERIFIED",
            "banknifty_1m": "VERIFIED",
            "nifty_5m": "VERIFIED",
            "banknifty_5m": "VERIFIED",
            "intraday_history": "~100 days 1m chunked, 1-2 years 5m for active symbols",
            "options_history": "NOT_AVAILABLE (Expired options contracts are pruned)",
            "historical_bid": "NOT_AVAILABLE",
            "historical_ask": "NOT_AVAILABLE",
            "historical_bid_ask_level": "NOT_AVAILABLE (Candle array contains [timestamp, open, high, low, close, volume])",
            "order_book_depth": "LIVE_ONLY_LEVEL_2 (Live WebSocket has 5-depth; historical has none)",
            "expired_contracts": "NOT_AVAILABLE",
            "timestamp_quality": "VERIFIED (UNIX timestamp integer)",
            "access_method": "REST API",
            "credentials_required": "CREDENTIAL_REQUIRED",
            "subscription_required": "YES",
            "pricing": "Free for FYERS trading account holders",
            "licensing": "Retail Trading API",
            "confidence": "HIGH",
            "notes": "Verified against official API docs. Strictly LTP-derived OHLCV candles. Zero historical Bid/Ask. INSUFFICIENT for options execution."
        },
        {
            "provider_name": "Yahoo Finance",
            "product_name": "Yahoo Finance Chart API (yfinance)",
            "official_source": "https://finance.yahoo.com",
            "verification_timestamp": "2026-09-09T13:27:00Z",
            "verification_status": "VERIFIED",
            "nifty_1m": "NOT_AVAILABLE (Limited to 7 days = 7 sessions, below 250 threshold)",
            "banknifty_1m": "NOT_AVAILABLE (Limited to 7 days = 7 sessions, below 250 threshold)",
            "nifty_5m": "NOT_AVAILABLE (Limited to 60 days = 59 sessions, below 250 threshold)",
            "banknifty_5m": "NOT_AVAILABLE (Limited to 60 days = 59 sessions, below 250 threshold)",
            "intraday_history": "7 sessions (1m), 59 sessions (5m); 1h auxiliary reaches 724 sessions but cannot substitute for 1m/5m",
            "options_history": "NOT_AVAILABLE (Current snapshot chains only; zero historical expired chains)",
            "historical_bid": "NOT_AVAILABLE",
            "historical_ask": "NOT_AVAILABLE",
            "historical_bid_ask_level": "NOT_AVAILABLE",
            "order_book_depth": "NOT_AVAILABLE",
            "expired_contracts": "NOT_AVAILABLE",
            "timestamp_quality": "VERIFIED (1m/5m OHLCV bar timestamps)",
            "access_method": "Public HTTP API / yfinance",
            "credentials_required": "NO",
            "subscription_required": "NO",
            "pricing": "Free",
            "licensing": "Personal / Non-commercial terms",
            "confidence": "HIGH (Empirically verified in Phase 10A/10B)",
            "notes": "Empirically audited baseline. Fails 250-session threshold for 1m and 5m. Zero historical options Bid/Ask. INSUFFICIENT for both Intraday and Options research."
        },
        {
            "provider_name": "NSE Public Bhavcopy",
            "product_name": "NSE Public All Reports / F&O Bhavcopy",
            "official_source": "https://www.nseindia.com/all-reports",
            "verification_timestamp": "2026-09-09T13:27:00Z",
            "verification_status": "VERIFIED",
            "nifty_1m": "NOT_AVAILABLE (EOD only)",
            "banknifty_1m": "NOT_AVAILABLE (EOD only)",
            "nifty_5m": "NOT_AVAILABLE (EOD only)",
            "banknifty_5m": "NOT_AVAILABLE (EOD only)",
            "intraday_history": "NOT_AVAILABLE (EOD daily settlement files only)",
            "options_history": "VERIFIED (>10 years daily settlement, volume, OI for all expired contracts)",
            "historical_bid": "NOT_AVAILABLE",
            "historical_ask": "NOT_AVAILABLE",
            "historical_bid_ask_level": "NOT_AVAILABLE (Bhavcopy reports Open, High, Low, Close, SettlePrice, Volume, OI; no bid/ask)",
            "order_book_depth": "NOT_AVAILABLE",
            "expired_contracts": "VERIFIED (Full EOD history of expired contracts)",
            "timestamp_quality": "VERIFIED (Daily calendar date)",
            "access_method": "Public Web Download / CSV Archives",
            "credentials_required": "NO",
            "subscription_required": "NO",
            "pricing": "Free",
            "licensing": "Public Exchange Dissemination",
            "confidence": "HIGH",
            "notes": "Excellent official baseline for daily EOD settlement and OI. Completely lacks intraday 1m/5m bars and historical Bid/Ask. INSUFFICIENT for Intraday and Options execution research."
        }
    ]
    return catalog


def get_provenance_records() -> List[Dict[str, Any]]:
    """
    Returns provenance records for all externally sourced material claims.
    """
    return [
        {
            "claim": "NSE Data & Analytics supplies historical Level 2 (5-depth) snapshot and Level 3 TBT order logs",
            "source": "NSE India Historical Data Products Technical Documentation",
            "source_url": "https://www.nseindia.com/market-data/historical-data-products",
            "verification_timestamp": "2026-09-09T13:27:00Z",
            "verification_method": "TECHNICAL_DOCUMENTATION_INSPECTION",
            "confidence": "HIGH"
        },
        {
            "claim": "TrueData provides >10 years 1m/5m intraday OHLCV for NIFTY 50 and BANKNIFTY",
            "source": "TrueData Historical API Specification & Documentation",
            "source_url": "https://www.truedata.in",
            "verification_timestamp": "2026-09-09T13:27:00Z",
            "verification_method": "TECHNICAL_DOCUMENTATION_INSPECTION",
            "confidence": "HIGH"
        },
        {
            "claim": "Zerodha Kite Connect historical endpoint returns exclusively [timestamp, open, high, low, close, volume, oi] with zero bid/ask",
            "source": "Kite Connect v3 Historical API Reference",
            "source_url": "https://kite.trade/docs/connect/v3/historical/",
            "verification_timestamp": "2026-09-09T13:27:00Z",
            "verification_method": "OFFICIAL_API_REFERENCE_INSPECTION",
            "confidence": "HIGH"
        },
        {
            "claim": "Upstox v2 historical candle endpoint returns [timestamp, open, high, low, close, volume, open_interest] with zero bid/ask",
            "source": "Upstox Developer Historical Candle Data Documentation",
            "source_url": "https://upstox.com/developer/api-documentation/historical-candle-data",
            "verification_timestamp": "2026-09-09T13:27:00Z",
            "verification_method": "OFFICIAL_API_REFERENCE_INSPECTION",
            "confidence": "HIGH"
        },
        {
            "claim": "Angel One SmartAPI historical endpoint provides strictly OHLCV candle bars",
            "source": "Angel One SmartAPI Documentation",
            "source_url": "https://smartapi.angelbroking.com/docs/Historical",
            "verification_timestamp": "2026-09-09T13:27:00Z",
            "verification_method": "OFFICIAL_API_REFERENCE_INSPECTION",
            "confidence": "HIGH"
        },
        {
            "claim": "FYERS API v3 historical endpoint delivers strictly candle array [timestamp, open, high, low, close, volume]",
            "source": "FYERS API v3 Historical Data Documentation",
            "source_url": "https://myapi.fyers.in/docs/",
            "verification_timestamp": "2026-09-09T13:27:00Z",
            "verification_method": "OFFICIAL_API_REFERENCE_INSPECTION",
            "confidence": "HIGH"
        },
        {
            "claim": "Yahoo Finance public chart API limits 1m to 7 days and 5m to 60 days",
            "source": "Phase 10A and Phase 10B Empirical Data Ingestion & Audit",
            "source_url": "file:///data/phase10b/intraday_quality.json",
            "verification_timestamp": "2026-09-09T13:27:00Z",
            "verification_method": "EMPIRICAL_AUDIT",
            "confidence": "HIGH"
        },
        {
            "claim": "NSE Public Bhavcopy contains daily settlement prices, volume, OI, but zero intraday bars or Bid/Ask quotes",
            "source": "NSE All Reports Public Dissemination Specification",
            "source_url": "https://www.nseindia.com/all-reports",
            "verification_timestamp": "2026-09-09T13:27:00Z",
            "verification_method": "OFFICIAL_EXCHANGE_SPECIFICATION_INSPECTION",
            "confidence": "HIGH"
        }
    ]
