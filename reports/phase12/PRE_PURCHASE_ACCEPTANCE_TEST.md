# Pre-Purchase Sample Data Acceptance Test Specification

Before executing any commercial agreement or issuing payment, the platform must receive a representative sample dataset from the candidate vendor. The sample will be audited via the canonical `DataOnboardingValidator`.

## 1. Sample Dataset Scope Requested
- **Intraday Sample**: Exactly 10 continuous trading sessions of 1-minute and 5-minute bars for NIFTY 50 and NIFTY BANK including a high-volatility session (e.g. Budget Day or RBI Policy Day).
- **Options Sample**: Exactly 5 consecutive trading days leading up to an expiry, covering all active and out-of-the-money strikes for NIFTY weekly/monthly options, containing continuous timestamped Bid and Ask quotes.

## 2. Intraday Validation Acceptance Suite
| Test ID | Validation Stage | Criterion | Failure Condition |
|---|---|---|---|
| **INT-01** | Schema Validation | All required columns present (`timestamp`, `open`, `high`, `low`, `close`, `volume`, `symbol`) | Missing column |
| **INT-02** | Timestamp Monotonicity | Timestamps strictly strictly increasing within each session | Out-of-order or duplicate timestamps |
| **INT-03** | Session Window | Exactly 375 1-minute bars per regular session (09:15-15:30 IST) | Unexpected session boundaries |
| **INT-04** | Missing Bars | Zero unannotated missing bars during regular trading hours | Unexplained missing minute intervals |
| **INT-05** | OHLC Sanity | `high >= max(open, close)` and `low <= min(open, close)` and all prices > 0 | Inverted bar geometry |
| **INT-06** | Volume Sanity | `volume >= 0` and integer values | Negative or NaN volume |
| **INT-07** | Timezone Verification | Explicit Asia/Kolkata (+05:30) or UTC ISO-8601 offset | Naive local timestamp |

## 3. Options Microstructure Acceptance Suite
| Test ID | Validation Stage | Criterion | Failure Condition |
|---|---|---|---|
| **OPT-01** | Microstructure Schema | `underlying`, `contract_id`, `expiry`, `strike`, `option_type`, `timestamp`, `bid`, `ask`, `ltp`, `volume`, `open_interest` | Missing schema field |
| **OPT-02** | Crossed Quotes | `bid <= ask` across 100% of paired quotes | Crossed quote (`bid > ask`) |
| **OPT-03** | Paired Timestamping | Bid and Ask recorded at synchronous timestamp | Unpaired or asynchronous quotes |
| **OPT-04** | Quote Continuity | $\ge 70.0\%$ continuous paired quote coverage throughout market hours (`PROJECT_RESEARCH_THRESHOLD`) | Sparse or sporadic coverage (< 70%) |
| **OPT-05** | Contract Validation | Expiry matches official exchange holiday calendar and contract master | Mismatched expiry weekday or date |
| **OPT-06** | Stale Quote Detection | Spread update interval under active market conditions $\le 5$ seconds | Frozen quote updates across hours |
| **OPT-07** | Market Depth Consistency | If Level 2 supplied: Best Bid $\ge$ Bid 2 $\ge$ Bid 3... and Best Ask $\le$ Ask 2... | Depth inversion |

## 4. Acceptance Action Protocol
- **PASS**: Dataset meets all thresholds. Proceed to commercial contract review.
- **FAIL**: Discrepancies logged. Detailed rejection report returned to vendor with formal request for rectified sample or commercial rejection.
