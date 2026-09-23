# PHASE 9.8 — CANDIDATE COMPARISON & ATTRIBUTION REPORT
Comparative analysis of all 8 candidate hypotheses evaluated under realistic transaction friction.

---

## 1. Full Economic Attribution Matrix

| Hypothesis ID | Name | Sample N | Gross Exp (bps) | Statutory Costs (bps) | Slippage (bps) | Net Exp (bps) | Annualized Sharpe | Max Drawdown | Verdict |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| `P98-H001` | 15-Minute Opening Range Breakout | 59 | -2.1 | 5.0 | 5.0 | -12.1 | -4.91 | -0.1% | **`INSUFFICIENT_DATA`** |
| `P98-H002` | Overnight Gap 30-Minute Mean-Reversion | 19 | -4.6 | 5.0 | 5.0 | -14.6 | -16.42 | 0.0% | **`INSUFFICIENT_DATA`** |
| `P98-H003` | 30-Minute Normalized Return Momentum | 765 | -0.7 | 5.1 | 5.1 | -10.8 | -32.25 | -15.2% | **`REJECTED`** |
| `P98-H004` | Intraday Volatility Compression Breakout | 413 | +0.2 | 5.0 | 5.0 | -9.8 | -17.03 | -8.5% | **`REJECTED`** |
| `P98-H005` | RBI MPC Policy Announcement 3-Session Drift | 13 | +28.2 | 5.0 | 5.0 | -49.2 | -9.92 | -4.2% | **`REJECTED`** |
| `P98-H006` | Cross-Sectional 20-Day Relative Strength Spread | 94 | -23.4 | 20.0 | 5.0 | -48.4 | -2.18 | -0.4% | **`REJECTED`** |
| `P98-H007` | Macro Regime Forecast Uncertainty Calibration | 450 | +0.0 | 0.0 | 0.0 | +0.0 | 0.00 | 0.0% | **`REJECTED`** |
| `P98-H008` | Options Historical Quotes Executable Boundary Audit | 15593 | +0.0 | 0.0 | 0.0 | +0.0 | 0.00 | 0.0% | **`INSUFFICIENT_DATA`** |

---

## 2. Friction Sensitivity & Stress Test Attribution

To ensure no false positives pass under understated transaction friction assumptions, each strategy was subjected to friction multipliers:

| Hypothesis ID | Net Exp (1.0x Baseline) | Net Exp (1.5x Stress) | Net Exp (2.0x Extreme Stress) | Friction Decay Assessment |
|:---|:---:|:---:|:---:|:---|
| `P98-H001` | -12.1 bps | -17.1 bps | -22.1 bps | High turnover fee sensitivity |
| `P98-H002` | -14.6 bps | -19.6 bps | -24.6 bps | High turnover fee sensitivity |
| `P98-H003` | -10.8 bps | -15.9 bps | -21.0 bps | High turnover fee sensitivity |
| `P98-H004` | -9.8 bps | -14.8 bps | -19.8 bps | High turnover fee sensitivity |
| `P98-H005` | -49.2 bps | +13.2 bps | +8.2 bps | High turnover fee sensitivity |
| `P98-H006` | -48.4 bps | -60.9 bps | -73.4 bps | High turnover fee sensitivity |
| `P98-H007` | +0.0 bps | +0.0 bps | +0.0 bps | High turnover fee sensitivity |
| `P98-H008` | +0.0 bps | +0.0 bps | +0.0 bps | High turnover fee sensitivity |

---

## 3. Candidate Summary & Disposition

Every candidate failed either on economic edge (gross alpha < transaction friction), statistical sample size, survivorship bias risk, or executable data availability. There are zero surviving candidates qualified for automated paper or live execution.
