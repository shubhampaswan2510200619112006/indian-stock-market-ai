# Phase 12 — Data Onboarding & Ingestion Validation Report

## 1. Automated 11-Stage Pipeline Execution
Every incoming or audited dataset is evaluated against the formal 11 stages:
1. INGEST
2. SCHEMA VALIDATION
3. TIMESTAMP VALIDATION
4. DUPLICATE CHECK
5. OHLC VALIDATION
6. CORPORATE ACTION VALIDATION
7. CONTRACT VALIDATION
8. BID/ASK VALIDATION
9. COVERAGE ANALYSIS
10. PROVENANCE RECORDING
11. READINESS GATE EVALUATION

## 2. Validation Run Summaries

### Dataset: `phase12_yahoo_intraday_1m_v1` (INTRADAY_1M)
- **Data Ready**: `False`
- **Options Quality Level**: `LEVEL_0`
- **Intraday Ready**: `False`
- **Stages Passed**: `1. INGEST, 2. SCHEMA VALIDATION, 3. TIMESTAMP VALIDATION, 4. DUPLICATE CHECK, 5. OHLC VALIDATION, 6. CORPORATE ACTION VALIDATION, 7. CONTRACT VALIDATION, 8. BID/ASK VALIDATION`
- **Stages Failed**: `9. COVERAGE ANALYSIS`
- **Rejection Reason**: `Intraday coverage (7 sessions) below 250 threshold`
- **Metrics**: `{'total_records': 2533, 'duplicate_records': 0, 'invalid_ohlc_count': 0, 'ohlc_valid_pct': 100.0, 'unique_sessions_count': 7, 'date_coverage_start': '2026-09-01', 'date_coverage_end': '2026-09-09'}`

### Dataset: `phase12_yahoo_intraday_5m_v1` (INTRADAY_5M)
- **Data Ready**: `False`
- **Options Quality Level**: `LEVEL_0`
- **Intraday Ready**: `False`
- **Stages Passed**: `1. INGEST, 2. SCHEMA VALIDATION, 3. TIMESTAMP VALIDATION, 4. DUPLICATE CHECK, 5. OHLC VALIDATION, 6. CORPORATE ACTION VALIDATION, 7. CONTRACT VALIDATION, 8. BID/ASK VALIDATION`
- **Stages Failed**: `9. COVERAGE ANALYSIS`
- **Rejection Reason**: `Intraday coverage (59 sessions) below 250 threshold`
- **Metrics**: `{'total_records': 4407, 'duplicate_records': 0, 'invalid_ohlc_count': 0, 'ohlc_valid_pct': 100.0, 'unique_sessions_count': 59, 'date_coverage_start': '2026-06-18', 'date_coverage_end': '2026-09-09'}`

### Dataset: `phase12_equity_reliance_v1` (DAILY)
- **Data Ready**: `True`
- **Options Quality Level**: `LEVEL_0`
- **Intraday Ready**: `False`
- **Stages Passed**: `1. INGEST, 2. SCHEMA VALIDATION, 3. TIMESTAMP VALIDATION, 4. DUPLICATE CHECK, 5. OHLC VALIDATION, 6. CORPORATE ACTION VALIDATION, 7. CONTRACT VALIDATION, 8. BID/ASK VALIDATION, 9. COVERAGE ANALYSIS, 10. PROVENANCE RECORDING, 11. READINESS GATE`
- **Metrics**: `{'total_records': 7704, 'duplicate_records': 0, 'invalid_ohlc_count': 0, 'ohlc_valid_pct': 100.0, 'unique_sessions_count': 7704, 'date_coverage_start': '1996-01-01', 'date_coverage_end': '2026-09-09'}`

### Dataset: `phase12_options_sqlite_sample_v1` (OPTIONS_QUOTES)
- **Data Ready**: `False`
- **Options Quality Level**: `LEVEL_2`
- **Intraday Ready**: `False`
- **Stages Passed**: `1. INGEST, 2. SCHEMA VALIDATION, 3. TIMESTAMP VALIDATION, 4. DUPLICATE CHECK, 5. OHLC VALIDATION, 6. CORPORATE ACTION VALIDATION, 7. CONTRACT VALIDATION, 8. BID/ASK VALIDATION, 9. COVERAGE ANALYSIS, 10. PROVENANCE RECORDING, 11. READINESS GATE`
- **Rejection Reason**: `Options execution data is LEVEL_2; Level 3/4 continuous paired surface required.`
- **Metrics**: `{'total_records': 842, 'duplicate_records': 0, 'total_quote_observations': 842, 'valid_bid_observations': 2, 'valid_ask_observations': 2, 'paired_bid_ask_observations': 2, 'crossed_market_observations': 0, 'paired_quote_coverage_pct': 0.24, 'continuous_executable_surface': 'UNSATISFIED', 'unique_sessions_count': 18, 'date_coverage_start': '2026-01-01', 'date_coverage_end': '2026-09-09'}`

