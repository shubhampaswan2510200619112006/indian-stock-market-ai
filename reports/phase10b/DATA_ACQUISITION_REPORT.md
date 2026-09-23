# PHASE 10B — DATA ACQUISITION EXPANSION REPORT

**Generated**: `2026-09-09T07:46:49.192975+00:00`  
**Phase**: `PHASE_10B_DATA_ACQUISITION_AND_VALIDATION`  

---

## 1. Data Sources Investigated

| Source Name | Access Type | Cost / Licensing | Status | Credentials Required? |
|:---|:---:|:---:|:---|:---:|
| Yahoo Finance Public Endpoint (yfinance) | `PUBLIC_UNAUTHENTICATED` | `FREE` | ACCESSIBLE_WITH_PROVIDER_SPECIFIC_RETENTION_LIMITS | `False` |
| NSE India Official Historical Archives (nseindia.com) | `PUBLIC_REGULATORY` | `FREE` | EOD_ONLY (Exchange provides daily Bhavcopy; multi-year 1m/5m historical bars not provided free) | `False` |
| NSE Data & Analytics Ltd (Official Market Data Feed) | `COMMERCIAL_EXCHANGE_FEED` | `PAID_COMMERCIAL_LICENSE` | STOPPED_UNDER_RULE_2 (Requires paid enterprise contract / subscription) | `True` |
| Broker APIs (Zerodha Kite Connect, Angel One SmartAPI, Upstox) | `BROKER_AUTHENTICATED_API` | `REQUIRES_BROKER_ACCOUNT_AND_API_SUBSCRIPTION` | STOPPED_UNDER_RULE_2 (Requires broker credentials and live account authorization) | `True` |

---

## 2. Intraday Data Acquisition & Granularity

> **Policy Statement**: 1-hour data may be retained as an auxiliary research dataset but cannot satisfy the 1m/5m confirmatory intraday readiness criterion unless that criterion is formally changed in a future preregistered phase.

| Instrument | Interval | Role | Sessions Observed | Total Bars | Target Required | Status |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| `NIFTY 50` | `1m` | `PRIMARY_HIGH_RESOLUTION` | 7 | 2,471 | 250 | **`OBSERVED_PROVIDER_RETENTION_LIMITED`** |
| `NIFTY 50` | `5m` | `PRIMARY_HIGH_RESOLUTION` | 59 | 4,395 | 250 | **`OBSERVED_PROVIDER_RETENTION_LIMITED`** |
| `NIFTY 50` | `1h` | `AUXILIARY_RESEARCH_ONLY` | 724 | 5,055 | 250 | **`OBSERVED_PROVIDER_RETENTION_LIMITED`** |
| `BANK NIFTY` | `1m` | `PRIMARY_HIGH_RESOLUTION` | 7 | 2,471 | 250 | **`OBSERVED_PROVIDER_RETENTION_LIMITED`** |
| `BANK NIFTY` | `5m` | `PRIMARY_HIGH_RESOLUTION` | 59 | 4,395 | 250 | **`OBSERVED_PROVIDER_RETENTION_LIMITED`** |
| `BANK NIFTY` | `1h` | `AUXILIARY_RESEARCH_ONLY` | 724 | 5,055 | 250 | **`OBSERVED_PROVIDER_RETENTION_LIMITED`** |

---
