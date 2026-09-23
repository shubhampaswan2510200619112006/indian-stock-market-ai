# PHASE 10A — COVERAGE & GRANULARITY AUDIT REPORT

**Status**: `BLOCKED / INSUFFICIENT_FOR_CONFIRMATORY`  
**Executive Conclusion**: Intraday research track is BLOCKED / INSUFFICIENT_FOR_CONFIRMATORY. Under current authorized public data sources, intraday historical depth is limited to the provider's observed rolling retention window (7d for 1m, 60d for 5m), yielding < 45 sessions. Confirmatory hypothesis testing requires >= 250 trading sessions. No synthetic bars will be generated, and no unauthorized purchases will be made.

---

## 1. Provider Availability & Observed Constraints

> **Important Scientific Boundary**: The stated Yahoo Finance 1m/5m retention limits are treated as *observed/provider-specific availability constraints for the selected public endpoint*. They must NOT be presented as a universal statement that multi-year intraday data cannot be obtained elsewhere.

### Empirically Observed Parameters & Coverage

| Instrument | Interval | Request Period | Sessions Returned | Rows Returned | Date Window | Target Target Sessions | Track Readiness |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `NIFTY 50` | `1m` | `7d` | 7 | 2,471 | 2026-09-01 to 2026-09-09 | 250 | **`AVAILABLE_BUT_INSUFFICIENT`** |
| `NIFTY 50` | `5m` | `60d` | 59 | 4,395 | 2026-06-18 to 2026-09-09 | 250 | **`AVAILABLE_BUT_INSUFFICIENT`** |
| `BANK NIFTY` | `1m` | `7d` | 7 | 2,471 | 2026-09-01 to 2026-09-09 | 250 | **`AVAILABLE_BUT_INSUFFICIENT`** |
| `BANK NIFTY` | `5m` | `60d` | 59 | 4,395 | 2026-06-18 to 2026-09-09 | 250 | **`AVAILABLE_BUT_INSUFFICIENT`** |

### Intraday Bar Integrity Metrics

| Instrument | Interval | Duplicate Count | Duplicate Rate | Missing Bar Rate | Median Gap | Max Intrasession Gap |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| `NIFTY 50` | `1m` | 0 | 0.0000 | 0.0587 | 1.0m | 1.0m |
| `NIFTY 50` | `5m` | 0 | 0.0000 | 0.0068 | 5.0m | 5.0m |
| `BANK NIFTY` | `1m` | 0 | 0.0000 | 0.0587 | 1.0m | 1.0m |
| `BANK NIFTY` | `5m` | 0 | 0.0000 | 0.0068 | 5.0m | 5.0m |

---
