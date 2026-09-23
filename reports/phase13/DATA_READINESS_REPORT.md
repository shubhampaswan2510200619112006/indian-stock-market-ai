# Data Readiness Gate Report

## 1. Aggregate Gate Overview
- **INTRADAY_1M_READY**: `BLOCKED`
- **INTRADAY_5M_READY**: `BLOCKED`
- **OPTIONS_LTP_READY**: `PASS`
- **OPTIONS_BID_ASK_READY**: `BLOCKED`
- **OPTIONS_EXECUTION_READY**: `BLOCKED`
- **PROVENANCE_READY**: `PASS`
- **LICENSE_READY**: `PASS`
- **DATA_QUALITY_READY**: `PASS`

## 2. Dataset-Scoped Readiness Breakdown
| Gate | Dataset ID | Underlying | State | Measured Value | Threshold | Reason |
|---|---|---|---|---|---|---|
| `OPTIONS_BID_ASK_READY` | `NSE_BHAVCOPY_OPTIONS_LTP_SAMPLE` | `NIFTY` | `BLOCKED` | `0.24% paired quotes, 0 crossed` | `>= 50.0% paired quote coverage (non-scattered)` | Scattered/isolated quotes only (< 50% paired coverage) |
| `OPTIONS_EXECUTION_READY` | `NSE_BHAVCOPY_OPTIONS_LTP_SAMPLE` | `NIFTY` | `BLOCKED` | `0.24% continuity (Level LEVEL_2)` | `>= 70.0% continuous paired surface (Level 3)` | Fails >= 70% continuous surface threshold |

## 3. Active Blocking Reasons
- INTRADAY_1M_READY is BLOCKED: Lacks qualified NIFTY and BANKNIFTY 1m datasets with >= 250 sessions.
- INTRADAY_5M_READY is BLOCKED: Lacks qualified NIFTY and BANKNIFTY 5m datasets with >= 250 sessions.
- OPTIONS_BID_ASK_READY is BLOCKED: No continuous paired Bid/Ask quote surface onboarded.
- OPTIONS_EXECUTION_READY is BLOCKED: Missing Level 3/4 continuous quote surface (>= 70% continuity).
