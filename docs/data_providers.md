# Data Providers Specification & Interface Architecture

## Overview
Phase 7 introduces explicit provider abstraction interfaces for market data, options chain feeds, news RSS streams, and underlying fundamentals. Every provider must report its capabilities truthfully via `ProviderCapabilities`.

---

## 1. Abstract Provider Interfaces (`src/ingestion/providers/base.py`)

### `ProviderCapabilities`
Standard metadata structure returned by every provider:
* `provider_name`: Human-readable provider identifier (e.g., `"YFinanceMarketProvider"`, `"NSELiveOptionsProvider"`).
* `supports_realtime`: `bool` indicating streaming/socket support.
* `is_delayed`: `bool` indicating whether feed is delayed.
* `delay_minutes`: `float` delay duration.
* `max_frequency_seconds`: `int` minimum update interval.
* `supported_symbols`: `List[str]` tickers supported.
* `supported_timeframes`: `List[str]` candle intervals supported (`"1m"`, `"5m"`, `"15m"`, `"1h"`, `"1d"`).
* `requires_authentication`: `bool`.
* `notes`: Additional capability notes.

---

## 2. Ingestion Providers

### A. Market Data Provider (`YFinanceMarketProvider`)
* **Module**: `src/ingestion/providers/market_provider.py`
* **Status Classification**: `DELAYED` (15-min delay on Yahoo Finance free tier) or `NEAR_REAL_TIME`.
* **Freshness Calculation**: Calculates age in seconds relative to current IST time. If age > 300s during market hours, status set to `STALE`.

### B. Options Data Provider (`NSELiveOptionsProvider`)
* **Module**: `src/ingestion/providers/options_provider.py`
* **Status Classification**: `UNAVAILABLE` when live exchange socket is unconfigured.
* **Truthfulness Requirement**: Zero fake options contracts or synthetic options chains are ever generated. If live feed is unconfigured, returns `OPTIONS STATUS: UNAVAILABLE`.

### C. Verified RSS News Provider (`VerifiedRSSNewsProvider`)
* **Module**: `src/ingestion/providers/news_provider.py`
* **Authority Level**: `PUBLIC_NEWS_FEED` (or `OFFICIAL_EXCHANGE` for BSE/NSE announcements).
* **Timestamps Recorded**:
  1. `published_at`: Original article publication timestamp from RSS feed.
  2. `received_at`: Timestamp when collector ingested the feed.
  3. `processed_at`: Timestamp when NLP entity mapping, event classification, and sentiment scoring completed.
* **Deduplication**: MD5 fingerprint of canonical URL or normalized title.

---

## 3. Data Status Taxonomy

| Status Label | Criteria |
| :--- | :--- |
| `REAL_TIME` | Latency <= 5s (Direct exchange socket stream) |
| `NEAR_REAL_TIME` | Latency 5s – 60s |
| `DELAYED` | Latency > 60s or provider explicitly delayed |
| `STALE` | Current time > provider timestamp + max TTL |
| `UNAVAILABLE` | Unconfigured feed in current environment |
| `ERROR` | Network or parsing error during fetch |
