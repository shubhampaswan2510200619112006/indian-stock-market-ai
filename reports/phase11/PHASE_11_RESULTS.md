# Phase 11: Empirical Results Report

## Untouched Out-of-Sample Performance Summary

| Hypothesis ID | Name | OOS N | Gross Exp (bps) | Statutory Friction | Brokerage | Slippage | Net Exp (bps) | OOS Sharpe | Win Rate | Classification |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `H11-001` | Cross-Sectional Momentum | 42 | -25.83 | 23.42 bps | 6.00 bps | 10.00 bps | **-65.25** | -1.37 | 42.9% | `INSUFFICIENT_DATA` |
| `H11-002` | Short-Term Reversal | 42 | +9.54 | 23.42 bps | 6.00 bps | 10.00 bps | **-29.88** | -0.67 | 45.2% | `INSUFFICIENT_DATA` |
| `H11-003` | Volatility-Adjusted Momentum | 42 | -19.87 | 23.42 bps | 6.00 bps | 10.00 bps | **-59.28** | -1.30 | 40.5% | `INSUFFICIENT_DATA` |
| `H11-004` | Volume/Turnover Confirmation | 42 | -66.14 | 23.42 bps | 6.00 bps | 10.00 bps | **-83.50** | -1.86 | 23.8% | `INSUFFICIENT_DATA` |
| `H11-005` | Relative Strength Persistence | 20 | -4.14 | 23.42 bps | 6.00 bps | 10.00 bps | **-43.56** | -0.43 | 40.0% | `INSUFFICIENT_DATA` |
| `H11-006` | Market-Breadth Conditioning | 42 | -22.36 | 23.42 bps | 6.00 bps | 10.00 bps | **-35.49** | -1.81 | 14.3% | `INSUFFICIENT_DATA` |

## Key Empirical Observations
1. **Gross Alpha vs Transaction Costs**: H11-002 (Short-Term Reversal) generated positive gross expectancy (+9.54 bps), but the round-trip friction (~39.42 bps) flipped net expectancy negative to -29.88 bps.
2. **Negative Gross Signals**: H11-001, H11-003, H11-004, H11-005, and H11-006 generated negative gross expectancies before any costs.
3. **Sample Size Notice**: In the untouched OOS window, non-overlapping rebalance counts were N=42 (for 5d holding period) and N=20 (for 10d holding period). Each fell below the project-defined minimum evaluation threshold (N < 60), resulting in `INSUFFICIENT_DATA`.
