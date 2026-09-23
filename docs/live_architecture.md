# Phase 7 Live Architecture & News Intelligence Terminal

## Architecture Diagram

```
                              ┌───────────────────────────────────┐
                              │  External Feeds & Market Data    │
                              │ (yfinance, Exchange RSS, News)   │
                              └─────────────────┬─────────────────┘
                                                │
                                                ▼
                              ┌───────────────────────────────────┐
                              │    Ingestion Provider Layer      │
                              │ (Market, Options, News Providers) │
                              └─────────────────┬─────────────────┘
                                                │
                                                ▼
                              ┌───────────────────────────────────┐
                              │        Live Market Service        │
                              │ (TTL Cache, Validation, Sanitizer)│
                              └─────────────────┬─────────────────┘
                                                │
                                                ▼
                              ┌───────────────────────────────────┐
                              │      Live Market Snapshot         │
                              │ (Quote, Candles, Multi-TF, News)  │
                              └───────┬───────────────────┬───────┘
                                      │                   │
                                      ▼                   ▼
     ┌──────────────────────────────────┐       ┌──────────────────────────────────┐
     │      AI Market Analyst           │       │    ML OOD Feature Drift Detector │
     │ (Structured JSON Synthesis)      │       │ (Z-Score Mahalanobis Monitoring) │
     └────────────────┬─────────────────┘       └─────────────────┬────────────────┘
                      │                                           │
                      └─────────────────┬─────────────────────────┘
                                        │
                                        ▼
                              ┌───────────────────────────────────┐
                              │    FastAPI REST & Streamlit UI    │
                              │   (Live Terminal, News, Health)   │
                              └───────────────────────────────────┘
```

---

## Key Components

### 1. Ingestion Provider Abstraction (`src/ingestion/providers/`)
Standardizes all market data, options feed, and news providers with `ProviderCapabilities`. Enforces status honesty (`REAL_TIME`, `NEAR_REAL_TIME`, `DELAYED`, `STALE`, `UNAVAILABLE`, `ERROR`).

### 2. Live Market Engine (`src/live_market/`)
* **Validator (`LiveDataValidator`)**: Checks OHLC sanity (e.g. High >= Low, Open > 0) and tags staleness based on timestamp age.
* **TTL Cache (`LiveDataCache`)**: Caches quotes and candles with controlled expiry times to prevent excessive provider calls.
* **Service (`LiveMarketService`)**: Orchestrates fetches and constructs unified aggregate `LiveMarketSnapshot`.

### 3. News Intelligence Engine (`src/news/`)
* **Deduplicator (`NewsDeduplicator`)**: Calculates canonical URL and normalized title MD5 fingerprints.
* **Entity Mapper (`EntityMapper`)**: Maps article content to ticker symbols (`NIFTY`, `BANKNIFTY`, `RELIANCE`, `TCS`, `INFY`, etc.) and sectors.
* **Event Classifier (`EventClassifier`)**: Categorizes news into `EARNINGS`, `REGULATORY`, `MACRO`, `RBI`, `GEOPOLITICAL`, `MANAGEMENT_CHANGE`, `GENERAL`.
* **Sentiment Analyzer (`NewsSentimentAnalyzer`)**: Generates rule-assisted directional sentiment score in `[-1.0, +1.0]`.
* **Impact Analyzer (`NewsImpactAnalyzer`)**: Evaluates post-event market price delta with explicit non-causal attribution caveats.

### 4. Event-Driven AI Analyst & Drift Detector (`src/ai_analyst/`)
* **AI Market Analyst (`AIMarketAnalyst`)**: Event-triggered LLM synthesis producing structured JSON output (`regime_summary`, `primary_bias`, `confidence`, `key_signals`, `key_risks`, `invalidation_condition`). Never invoked on every tick.
* **OOD Feature Drift Detector (`OODDetector`)**: Calculates Z-scores of incoming feature vectors against historical training baselines. Triggers `DRIFT_WARNING` or `OOD` status when features exceed 3.0 standard deviations.

---

## Safety & Compliance Boundaries

1. **NO Live Order Execution**: The platform contains ZERO live broker API connections or order routing logic.
2. **NO Profit Claims**: The UI explicitly displays Phase 6.5 research banner:
   `"MODEL RESEARCH STATUS: LIMITED DATA / INSUFFICIENT STATISTICAL EVIDENCE"`.
3. **Non-Causal News Impact**: All news market impact correlations explicitly state:
   *"Price change observed following event; attribution is uncertain."*
