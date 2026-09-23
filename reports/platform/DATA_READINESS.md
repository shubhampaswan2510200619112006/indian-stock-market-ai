# Data Readiness Audit & Capability Matrix

## Separation of Data Availability, Research Readiness, and Execution Readiness

| Capability ID | Name | Physical Availability | Research Readiness | Execution Readiness | Quality Grade | Verified Coverage |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| `daily_index` | Daily Index OHLCV (NIFTY 50 / BANKNIFTY) | **YES** | `READY` | `NOT_APPLICABLE` | `RESEARCH_READY` | >=250 sessions (Satisfied: 495 sessions) |
| `cross_sectional_equities` | Cross-Sectional Daily Equity Panels | **YES** | `READY` | `NOT_APPLICABLE` | `RESEARCH_READY` | >=50 constituents, >=250 sessions (Satisfied) |
| `intraday_1m` | Intraday 1-Minute OHLCV (NIFTY 50 / BANKNIFTY) | **YES** | `BLOCKED` | `BLOCKED` | `INSUFFICIENT_HISTORY` | >=250 trading sessions (Available: 7 sessions) |
| `intraday_5m` | Intraday 5-Minute OHLCV (NIFTY 50 / BANKNIFTY) | **YES** | `BLOCKED` | `BLOCKED` | `INSUFFICIENT_HISTORY` | >=250 trading sessions (Available: 59 sessions) |
| `historical_options_ltp` | Historical Options LTP / Settlement / Open Interest | **YES** | `LIMITED` | `BLOCKED` | `EOD_LTP_SETTLEMENT` | Permitted for theoretical IV / volatility research; strictly blocked for trade execution |
| `historical_options_bid_ask` | Historical Options Executable Bid/Ask Quotes | **NO** | `BLOCKED` | `BLOCKED` | `NO_GENUINE_EXECUTABLE_HISTORY` | Requires verified Level 2 paired quotes from approved exchange or data redistributor |
| `continuous_options_quote_surface` | Continuous Options Executable Quote Surface (Level 3/4) | **NO** | `BLOCKED` | `BLOCKED` | `BLOCKED` | Requires Level 3/4 continuous timestamped Bid/Ask across trading hours and strike spectrum |

## Detailed Capability Analysis

### 1. Ready Datasets (Active Research Foundation)
- **Daily Index OHLCV**: Fully verified (>495 sessions across NIFTY 50 and BANKNIFTY). Approved for macro-regime, daily trend, and volatility calibration research.
- **Cross-Sectional Equities**: 50 constituents across >504 trading sessions. Approved for cross-sectional dispersion, relative strength, and risk modeling.

### 2. Blocked Intraday Datasets (Insufficient Coverage)
- **Intraday 1-Minute**: 7 sessions available vs. 250 required $\to$ `RESEARCH_BLOCKED`.
- **Intraday 5-Minute**: 59 sessions available vs. 250 required $\to$ `RESEARCH_BLOCKED`.
- **Policy**: Research modules attempting confirmatory analysis on truncated intraday series are rejected automatically by `ReadinessGate`.

### 3. Blocked Options Execution Datasets (Microstructural Gaps)
- **Historical Options Settlement/LTP**: 17,607 records available. Approved strictly for implied volatility / theoretical pricing research (`RESEARCH_LIMITED`).
- **Historical Options Bid/Ask**: 0 genuine exchange paired quotes. Classified as `NO_GENUINE_EXECUTABLE_HISTORY`.
- **Continuous Surface Coverage**: 0.0%. Classified as `BLOCKED`. All execution backtests are strictly prohibited until genuine Level 3/4 continuous quote data is onboarded.
