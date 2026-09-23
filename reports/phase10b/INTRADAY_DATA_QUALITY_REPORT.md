# PHASE 10B — INTRADAY DATA QUALITY REPORT

**Audit Status**: `INTRADAY_RESEARCH_READY = BLOCKED`  

---

## 1. Preregistered Confirmatory Evaluation (Correction 1)

- **Requirement**: >= 250 trading sessions of 1m or 5m bars for both NIFTY and BANKNIFTY
- **NIFTY 1m Sessions**: 7
- **NIFTY 5m Sessions**: 59
- **BANKNIFTY 1m Sessions**: 7
- **BANKNIFTY 5m Sessions**: 59
- **Auxiliary 1h Sessions**: 724 (Auxiliary research only; cannot substitute for 1m/5m)
- **Criteria Met**: `False`

## 2. Bar Quality & Invariant Audits

| Series | Interval | Total Bars | Monotonic? | Duplicates | OHLC Violations | Boundary Violations | Verdict |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `NIFTY 50` | `1m` | 2,471 | `True` | 0 | 0 | 0 | **`CLEAN`** |
| `NIFTY 50` | `5m` | 4,395 | `True` | 0 | 0 | 0 | **`CLEAN`** |
| `NIFTY 50` | `1h` | 5,055 | `True` | 0 | 0 | 0 | **`CLEAN`** |
| `BANK NIFTY` | `1m` | 2,471 | `True` | 0 | 0 | 0 | **`CLEAN`** |
| `BANK NIFTY` | `5m` | 4,395 | `True` | 0 | 0 | 0 | **`CLEAN`** |
| `BANK NIFTY` | `1h` | 5,055 | `True` | 0 | 0 | 0 | **`CLEAN`** |

---
