# Phase 12 — Data Acquisition Specification & Quality Thresholds

## 1. Executive Summary
This document formalizes the rigorous criteria and project-defined thresholds required to remove the platform's two primary data limitations: multi-year intraday index data and historical options execution data.

### Absolute Governance Invariants
- `PURCHASE_AUTHORIZED = FALSE`: Zero commercial subscriptions or payments without explicit human authorization.
- `HUMAN_DECISION_REQUIRED = TRUE`: Human operator must review and confirm acquisition proposals.
- `DATA_FABRICATION_PROHIBITED = TRUE`: Zero synthetic Bid/Ask quotes or continuous surfaces labeled as genuine.

## 2. Intraday Requirements Specification
| Requirement | Specification | Threshold Type |
|---|---|---|
| **Target Symbols** | `NIFTY 50, NIFTY BANK` | Core Index Benchmarks |
| **Intervals** | `1m, 5m` | No daily/hourly substitution permitted |
| **Minimum Sessions** | `N >= 250` | `PROJECT_RESEARCH_THRESHOLD` (1 Year Min) |
| **Preferred Coverage** | `3-5 years (~750-1250 sessions)` | Target Multi-Year Horizon |
| **Timezone** | `Asia/Kolkata (+05:30)` | Official Exchange Session Hours |
| **Session Hours** | `09:15:00 - 15:30:00` | Regular NSE Cash/F&O Hours |

## 3. Options Requirements Specification
| Requirement | Specification | Threshold Type |
|---|---|---|
| **Target Underlyings** | `NIFTY, BANKNIFTY` | Liquid Index Options |
| **Required Fields** | `underlying, contract_id, expiry, strike, option_type, timestamp, bid, ask, ltp, volume, open_interest` | Full Microstructure Envelope |
| **Paired Quote Continuity** | `>= 70.0%` | `PROJECT_RESEARCH_THRESHOLD` for Level 3 |
| **Contract Validation** | `EXCHANGE_SPEC_AND_CALENDAR_DRIVEN` | Exchange spec & holiday calendar driven |

### Options Quality Hierarchy (L0–L4)
- **LEVEL_0**: NO OPTIONS DATA
- **LEVEL_1**: LTP / SETTLEMENT ONLY
- **LEVEL_2**: ISOLATED BID/ASK
- **LEVEL_3**: CONTINUOUS PAIRED BID/ASK (Execution-Ready for Research)
- **LEVEL_4**: DEPTH / ORDER-BOOK CAPABLE
