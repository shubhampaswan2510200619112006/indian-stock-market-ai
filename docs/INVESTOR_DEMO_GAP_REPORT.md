# INVESTOR DEMO GAP REPORT & PRIORITIZED BLOCKERS
**Indian Options AI Platform — Technical Readiness & Deficiency Audit**
*Date: September 2026 | Milestone: Investor Demo Hardening | Governance: Zero-Cost Policy Active*

---

## 1. Executive Summary & Audit Mandate

This report identifies the **exact remaining technical and data blockers** required to transition the platform from its current demonstrator state into an institutional-grade production system.

Every gap is classified into a strict priority hierarchy:
- **P0 (Correctness & Safety)**: System invariants, mathematical precision, absence of misleading claims.
- **P1 (Investor-Critical Evidence)**: Data and statistical barriers preventing verified alpha demonstration.
- **P2 (Useful Platform Enhancements)**: Infrastructure, persistence, and live data quality upgrades.
- **P3 (Cosmetic & UI Polish)**: Non-blocking visual and interactivity improvements.

---

## 2. Prioritized Gap Matrix

### P0 — Mathematical Correctness & Safety (100% RESOLVED IN PHASE 17A)
| Gap ID | Subsystem | Description | Resolution Status | Verified Location |
|---|---|---|---|---|
| **P0-01** | **Safety Invariant** | Hard architectural block against live broker execution. | **RESOLVED** | `src/paper_trading/execution_guard.py` enforces `ALLOW_LIVE_EXECUTION = False` compile-time constant. |
| **P0-02** | **Test Suite Stability** | Regression test failures in Bhavcopy, Kite regex, and paper trading fill timestamps. | **RESOLVED** | All **658 / 658 unit & integration tests pass (100%)** with zero failures. |
| **P0-03** | **Options Quote Truth** | Synthetic Bid/Ask fills manufactured from LTP. | **RESOLVED** | `fill_engine.py` strictly refuses options fills (`OPTIONS_DATA_UNAVAILABLE`). `CONTINUOUS_EXECUTABLE_SURFACE = 0.0%` prominently disclosed. |
| **P0-04** | **Probability Mislabeling** | Presenting deterministic heuristic rule scores as statistical probabilities. | **RESOLVED** | All UI components explicitly label heuristic scores as *Rule-Based Alignment / Match Scores (Not Empirical Probabilities)*. |
| **P0-05** | **Subjective Scoring** | Hard-coding an arbitrary "8.2 / 10" overall readiness score. | **RESOLVED** | Retired subjective scores. Replaced with objective evidence-based readiness tables. |

---

### P1 — Investor-Critical Evidence Blockers (Data-Dependent)
| Gap ID | Blocker Area | Technical Deficiency | Impact on Investor Presentation | Exact Solution Required |
|---|---|---|---|---|
| **P1-01** | **Historical Options Quote Depth** | Quote store has 15,106 quotes but only 102 paired Bid/Ask observations (0.68% coverage). Continuous executable surface is **0.0%**. | **Execution-realistic options backtesting is strictly BLOCKED.** Cannot demonstrate live-equivalent option strategy PnL. | Acquire 3+ years of continuous 1-min / 5-min options quote book from an authorized vendor (TruData or GDFL). |
| **P1-02** | **Multi-Year Intraday Underlying History** | Free yfinance intraday endpoint is limited to 60 days (~59 trading sessions), falling short of confirmatory sample size gates ($N \ge 60$). | Intraday momentum, opening range breakouts (ORB), and volatility compression remain classified as **EXPLORATORY_ONLY**. | Acquire 2–5 years of 1-min & 5-min OHLCV bars for NIFTY & BANKNIFTY via retail broker API or commercial feed. |
| **P1-03** | **Index Continuous Dividend Yield ($q$)** | Black-Scholes pricing engine defaults to $q = 0.0$. | Slight upward bias on call option prices and downward bias on puts for long-dated contracts ($T > 30\text{d}$). | Ingest continuous rolling dividend yield for NIFTY 50 ($\sim 1.1\% - 1.3\%$) into `pricing.py`. |
| **P1-04** | **Dynamic OOD Baseline Calibration** | `OODDetector` previously relied on preset statistical parameters rather than dynamic fitting. | Feature drift thresholds are static rather than tailored to the current historical volatility regime. | Parameterize OOD baseline calculations dynamically from the rolling 252-day in-sample training window. |

---

### P2 — Useful Platform Enhancements (Non-Blocking)
| Gap ID | Subsystem | Proposed Enhancement | Implementation Effort | Value to Investor Demo |
|---|---|---|---|---|
| **P2-01** | **Live Broker Feed** | Configure Zerodha Kite Connect or Upstox API token for live Level 2 (Best 5) depth during 09:15–15:30 IST. | Low (Stubs already exist in `src/ingestion/`). Requires funded account. | Demonstrates real-time WebSocket order-book updates in live market session. |
| **P2-02** | **Historical Bhavcopy Archive** | Batch download 2020–2026 official NSE F&O Bhavcopy files into compressed Parquet/SQLite tables. | Low (Downloader verified in `bhavcopy_downloader.py`). | Provides 6 full years of historical EOD option chains, PCR, and Max Pain history. |
| **P2-03** | **India VIX Continuous Pipeline** | Ingest daily historical India VIX into feature engine and calculate rolling IV Percentile and Rank. | Low (Fetcher logic implemented in `macro_features_fetcher.py`). | Replaces realized-volatility proxy with authentic market implied fear gauge. |
| **P2-04** | **Model Weight Versioning** | Implement persistent model registry (`models/registry/`) with versioned serialized artifacts and calibration curves. | Medium. | Allows investors to audit trained model weights without re-training each session. |

---

### P3 — Cosmetic & UI Polish (Low Priority)
| Gap ID | Subsystem | Description | Target Polish |
|---|---|---|---|
| **P3-01** | **Streamlit State Push** | Dashboard currently relies on periodic auto-refresh or manual refresh button. | Transition to real-time event-driven state push via WebSocket connections. |
| **P3-02** | **3D Volatility Surface** | Plotly 3D volatility surface is static interactive mesh. | Add surface lighting, contour level shading, and animated term-structure evolution. |
| **P3-03** | **Interactive Scenario Slider** | Strategy payoff analysis requires re-running scenario matrix. | Add real-time slider adjusting underlying price $\pm 5\%$ with dynamic Greeks rebalancing. |

---

## 3. Summary Roadmap for Institutional Launch

```
[ Current State: Phase 17A Investor Baseline ]
  ├── 658 / 658 Tests Passing (100%)
  ├── Black-Scholes & Greeks Mathematically Proven
  ├── Full Indian Statutory Cost Model Active
  ├── Hard Safety Locks & Zero Real-Money Execution
  └── Truth-in-Advertising Investor Due Diligence Portal Active
            │
            ▼ (Next Milestone: Data Acquisition)
[ Phase 18: Commercial Data Ingestion ]
  ├── Ingest 3+ Years Historical Options Bid/Ask (TruData / GDFL)
  ├── Backfill 5-Year 1-Minute Intraday NIFTY / BANKNIFTY Panel
  └── Unlock Execution-Realistic Backtesting Engine
            │
            ▼ (Final Milestone: Production Research)
[ Phase 19: Confirmatory Edge & Strategy Deployment ]
  ├── Retest Pre-Registered Hypotheses on Certified Dataset
  ├── Deploy Calibrated Walk-Forward ML Classifiers
  └── Institutional Portfolio Allocation & Paper Trading Validation
```
