# INVESTOR TECHNICAL DUE DILIGENCE Q&A
**Indian Options AI Platform — Direct, Evidence-Based Responses to Hard Questions**
*Milestone: 17.0.0-INVESTOR-FROZEN | Standard: Institutional Quantitative Review*

---

### Q1: What data do you actually have in the repository right now?
**Answer**:
We have:
1. **Official NSE Bhavcopy EOD Archives**: Daily equity and derivatives closing summaries from 2020 to 2026, stored in SQLite tables (`data/indian_options.db`) containing 25,864 options quotes and 477 options contracts across NIFTY and BANKNIFTY.
2. **Yahoo Finance Daily & Intraday Cash Panels**: Continuous daily OHLCV for NIFTY, BANKNIFTY, FINNIFTY, and key equities (1,009 daily bars), plus a trailing 60-day window of delayed 5-minute intraday bars (~59 sessions, 4,425 bars).
3. **Historical Options Settlement Panel**: 15,106 historical options quotes, of which 102 contain paired Bid/Ask observations.
4. **Macroeconomic Benchmarks**: Historical India VIX daily closing data and statutory RBI rate series.

We do **NOT** have multi-year tick-level options order books or commercial high-frequency intraday feeds.

---

### Q2: How much historical data does the platform cover?
**Answer**:
- **EOD Equity & Derivatives**: ~5 years (2020–2026).
- **Intraday Cash Index Bars (5m)**: ~59 sessions (trailing 60-day public limit).
- **Historical Executable Options Quotes**: 102 paired Bid/Ask observations (0.68% coverage).

Because the trailing intraday panel ($N=59$) fell short of our pre-registered confirmatory sample size gate ($N \ge 60$), all intraday alpha strategies were classified strictly as `EXPLORATORY_ONLY`.

---

### Q3: How are options priced and Greeks calculated?
**Answer**:
Index options are priced using the analytical **Black-Scholes-Merton (1973)** formula for European options:
- **Cumulative Normal Distribution**: Evaluated using `scipy.stats.norm.cdf` (machine precision $\sim 10^{-16}$).
- **Put-Call Parity**: Verified analytically across strike grids ($< 10^{-12}$ error).
- **Greeks Units**:
  - Delta ($\Delta$): Direct $[-1, 1]$
  - Gamma ($\Gamma$): Change in delta per 1 index point move
  - Theta ($\Theta$): Scaled by $1/365$ (calendar day time decay)
  - Vega ($\nu$): Scaled by $1/100$ (price change per 1% change in IV)
  - Rho ($\rho$): Scaled by $1/100$ (price change per 1% change in $r$)
- **Implied Volatility Solver**: Dual-engine Newton-Raphson quadratic solver with Brent's bracketed root-finder fallback, resolving IV to absolute tolerance $\le 10^{-5}$ with pre-flight no-arbitrage bounds checks.

---

### Q4: Do you have historical Bid/Ask for options?
**Answer**:
**No, not in continuous form.** 
Out of 15,106 historical options records in the research database:
- `VALID_PAIRED_BID_ASK_QUOTES = 102`
- `PAIRED_QUOTE_OBSERVATION_COVERAGE = 0.68%`
- `CONTINUOUS_EXECUTABLE_SURFACE_COVERAGE = 0.0%`

The remaining 99.32% of records are settlement prices or Last Traded Prices (LTP). We **strictly refuse** to fabricate synthetic Bid/Ask spreads from LTP.

---

### Q5: Can the system backtest executable options strategies right now?
**Answer**:
**No. Historical options execution backtesting is strictly BLOCKED.**
Because options execution in live markets incurs significant spread friction (1% to 10% of premium), running backtests on settlement or LTP prices produces an illusion of profitability that collapses in production. Until a commercial continuous Bid/Ask tick dataset is acquired, options execution backtesting remains locked.

---

### Q6: How is probability calibrated?
**Answer**:
Raw machine learning outputs (such as tree ensemble scores) are **not** probabilities. We apply:
1. **Platt Scaling**: Univariate logistic sigmoid fitted on out-of-fold validation margins:
   $$P(Y = 1 \mid s) = \frac{1}{1 + \exp(A \cdot s + B)}$$
2. **Isotonic Regression**: Non-parametric monotonic step function via the Pair Adjacent Violators algorithm.

Calibrators are fitted strictly on validation partitions, never on training data and never on the test set. Calibrated outputs are validated using the **Brier Score** and **Expected Calibration Error (ECE)** against market climatology.

---

### Q7: How do you prevent look-ahead bias and data leakage?
**Answer**:
We enforce four structural leakage invariants:
1. **Strict Forward Targets**: Labels are computed strictly as $R_{t \to t+h} = \frac{\text{Close}_{t+h}}{\text{Close}_t} - 1$. Target columns are stripped before feature extraction.
2. **In-Fold Scaling**: All feature transformers (`StandardScaler`, `RobustScaler`) are fitted exclusively on the in-sample training fold.
3. **Purge Windows**: When forecasting over an $h$-day horizon, sample rows $[T_{\text{split}} - h, T_{\text{split}}]$ are dropped from the training set to prevent overlapping target contamination.
4. **Embargo Windows**: A 2 to 5-day embargo is inserted immediately after the test partition to eliminate autoregressive serial correlation leakage.

---

### Q8: What were your out-of-sample (OOS) research results?
**Answer**:
In our frozen Phase 9.8 evaluation of 8 pre-registered hypotheses:
- Directional 1-day OOS accuracy hovered around 50.8% (against a naive buy-and-hold base rate of ~57.8%).
- Gross expectancy was marginally positive in some tracks (+0.2 to +28 bps).
- However, after applying full Indian statutory costs and realistic spread slippage, **net expectancy was negative across all tradable tracks** (-10 to -49 bps per trade).
- **Surviving Confirmatory Candidates**: **0 / 8**.
- **Conclusion**: `NO_DEMONSTRATED_EDGE` / `PHASE_10_NOT_JUSTIFIED`.

---

### Q9: What happened to failed hypotheses? Were they discarded?
**Answer**:
**No. Every failed hypothesis is permanently cataloged and preserved in the repository.**
All 8 hypotheses (`P98-H001` through `P98-H008`) remain frozen in `data/research_hypothesis_registry.json` and documented in `PHASE_9_8_RESEARCH_REPORT.md`. We do not remove failed tests or alter parameters to make backtests look better. Preserving failed experiments prevents duplicate research and protects against p-hacking.

---

### Q10: Can the system trade automatically with real money?
**Answer**:
**No. Live real-money trading is architecturally impossible in this codebase.**
`src/paper_trading/execution_guard.py` enforces a compile-time constant:
```python
ALLOW_LIVE_EXECUTION: bool = False
```
Any attempt to invoke live broker execution raises `LiveExecutionDisabledError`. No order placement, order modification, or real-money API endpoints exist. The platform is strictly an intelligence, risk, and paper-trading terminal.

---

### Q11: What happens when market data is missing or stale?
**Answer**:
The platform enforces the **Abstention Principle**:
- If data is older than configured thresholds, it is flagged as `STALE`.
- If an order update has a timestamp older than order submission, the fill engine rejects it with `RETROACTIVE_FILL_REJECTED`.
- If Bid or Ask quotes are absent, execution is refused (`NO_VALID_EXECUTABLE_QUOTE`).
- The system comfortably outputs `NO_TRADE`, `INSUFFICIENT_DATA`, or `OUT_OF_DISTRIBUTION`.

---

### Q12: How do you handle model drift and regime changes?
**Answer**:
1. **Market Regime Engine**: Synthesizes NIFTY trend, BANKNIFTY confirmation, ATR, realized volatility, and India VIX to classify the market into 6 regime states (*Strong Bull, Bull, Sideways, Bear, Strong Bear, High Volatility*).
2. **Out-of-Distribution (OOD) Detector**: Evaluates whether current market volatility and return distributions deviate more than 3 standard deviations from baseline distributions. When OOD is detected, strategy candidate generation is halted.

---

### Q13: What exact capabilities would additional commercial data unlock?
**Answer**:
Acquiring authorized commercial tick-level data (e.g. from TruData or GlobalDataFeeds) would unlock:
1. **Execution-Realistic Options Backtesting**: Testing multi-leg spreads (Iron Condors, Straddles, Bull Spreads) against authentic historical Bid/Ask order books.
2. **Real-Time Paper Trading on Options**: Live fill simulation with queue priority against real-time Level 2 (Best 5) depth.
3. **Statistical Power**: Expanding intraday sample size from $N=59$ to $N > 1,000$ sessions to test whether opening drives or volatility compression have genuine statistical alpha.
