# IMPLEMENTATION & UPGRADE ROADMAP
**Indian Options AI Platform — Phase 17 Engineering Plan**
*Date: September 2026 | Milestone: Investor-Ready Analytical Platform*

---

## 1. Prioritization Framework

Our engineering and quantitative priorities are strictly ranked by investor impact, statistical honesty, and operational safety:

```
[ P0: Critical Governance & Test Fixes ]  ==> COMPLETE (658/658 Tests Passing)
                   │
                   ▼
[ P1: Core Quantitative Upgrades ]       ==> IN PROGRESS (Calibration & Edge Engine)
                   │
                   ▼
[ P2: Data Foundation & Features ]       ==> PLANNED (Bhavcopy Backfill & VIX Integration)
                   │
                   ▼
[ P3: UI Polish & Investor Presentation] ==> PLANNED (Executive Dashboard & Walkthroughs)
```

---

## 2. Exhaustive Prioritized Action Items

### P0 — Critical Governance & Stability (COMPLETED)
- [x] **P0-01: Stabilize Test Suite**: Fixed Bhavcopy downloader tests, Kite provider regex assertions, and paper trading fill timestamp sequencing (`658 passed, 0 failed`).
- [x] **P0-02: Hard-Lock Real Money Execution**: Enforced `ExecutionGuard` rejecting live mode unconditionally (`LiveExecutionDisabledError`).
- [x] **P0-03: Zero-Cost Governance Enforced**: Enforced `PURCHASE_AUTHORIZED=FALSE` and `AUTOMATED_VENDOR_CONTACT=DISABLED`.
- [x] **P0-04: Dashboard Crash Fixes**: Resolved parameter mismatches in `live_market.py` and keyword argument discrepancies in `live_news.py`.

---

### P1 — Core Analytical & Calibration Upgrades (Immediate Focus)
1. **Dynamic Probability Calibration Engine**:
   - *Target*: Wire Platt Scaling and Isotonic Regression into the real-time inference pipeline.
   - *Components*: `src/ml/calibrator.py`, `src/ai_analyst/analyst.py`.
   - *Deliverable*: Replace hard-coded confidence heuristics (`0.70/0.40`) with empirical out-of-sample posterior probabilities.
2. **Empirical Out-of-Distribution (OOD) Dynamic Baseline**:
   - *Target*: Replace static preset parameters in `src/ml/ood_detector.py` with dynamic reference statistics fitted directly on the rolling 252-day in-sample baseline window.
   - *Components*: `src/ml/ood_detector.py`.
3. **Persisted Trained ML Weights Pipeline**:
   - *Target*: Store serialized walk-forward model artifacts and calibration curves in a versioned model registry (`models/registry/`).
   - *Components*: `src/ml/model_registry.py`.

---

### P2 — Data Infrastructure & Feature Engine Completeness
1. **Automated Multi-Year NSE Bhavcopy Ingestion**:
   - *Target*: Download and index 2020–2026 EOD F&O Bhavcopy archives into SQLite/Parquet for 6-year historical options research.
   - *Components*: `src/ingestion/bhavcopy_downloader.py`.
2. **Continuous India VIX Pipeline**:
   - *Target*: Ingest historical and intraday India VIX series; compute rolling IV Percentile and IV Rank as primary ML features.
   - *Components*: `src/features/volatility.py`.
3. **Volume & Institutional Flow Engine Upgrade**:
   - *Target*: Implement full volume profile indicators (VWAP bands, Volume Spread Analysis, FII/DII rolling net flow).
   - *Components*: `src/features/volume.py`, `src/ingestion/nse_fii_dii.py`.
4. **Dynamic Index Dividend Yield ($q$)**:
   - *Target*: Calculate continuous rolling dividend yield for NIFTY 50 to eliminate call/put pricing asymmetry in Black-Scholes.
   - *Components*: `src/options/pricing.py`.

---

### P3 — Investor Presentation & UI Polish
1. **Executive Investor Overview Page**:
   - *Target*: Add a clean, C-level executive summary tab in the Streamlit dashboard summarizing platform health, model calibration, Sharpe ratios, and governance status at a single glance.
   - *Components*: `dashboard/pages/00_Executive_Overview.py`.
2. **Interactive Probability Calibration Visualizer**:
   - *Target*: Real-time Reliability Diagram and Brier Score comparison tool in the Streamlit UI comparing raw vs calibrated predictions.
   - *Components*: `dashboard/pages/09_Probability_Calibration.py`.
3. **Interactive Cost & Friction Calculator**:
   - *Target*: Visual tool allowing investors to adjust STT, slippage, and brokerage to see exact net PnL impact on trading strategies.
   - *Components*: `dashboard/pages/10_Cost_Model.py`.

---

## 3. "What Do I Need Right Now?" — Immediate Investor Readiness Checklist

If an investor demo is scheduled within 48 hours, here is the exact checklist:

1. **Verify All System Tests Are Passing**:
   ```bash
   python -m pytest tests/
   # Expected: 658 passed, 0 failed
   ```
2. **Launch Streamlit Dashboard**:
   ```bash
   streamlit run dashboard/app.py --server.port 8501
   ```
3. **Demonstrate High-Value Differentiators**:
   - **Greeks & IV Surface**: Real-time Newton-Raphson solver with arbitrage bounds.
   - **Cost Decomposition**: Complete Indian statutory tax breakdown (STT, GST, Stamp Duty).
   - **Walk-Forward Validation**: Purged & Embargoed cross-validation eliminating leakage.
   - **Governance Lock**: Refusal of live execution proves architectural maturity.
