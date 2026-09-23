# Phase 11: Preregistration Manifest

## Preregistration Contract
- **Status**: `PREREGISTRATION_LOCKED`
- **Timestamp**: `2026-09-09T13:50:00Z`
- **Total Hypotheses**: 6

## Master Preregistered Hypotheses

| ID | Name | Lookback | Holding | Ranking Rule | Economic Rationale |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `H11-001` | Cross-Sectional Momentum | 20d | 5d | Sort eligible constituents by R_i_20 in descending order | Information diffusion across market participants occurs with delay, causing medium-term top performers to outperform bottom performers. |
| `H11-002` | Short-Term Reversal | 5d | 5d | Sort eligible constituents by R_i_5 in ascending order (lowest return first) | Short-term extreme price moves driven by liquidity provision imbalances and retail overreaction tend to partially reverse over subsequent sessions. |
| `H11-003` | Volatility-Adjusted Momentum | 20d | 5d | Sort eligible constituents by VolAdjMom_i in descending order | Scaling momentum by realized historical volatility eliminates uncompensated idiosyncratic noise and improves signal information ratio. |
| `H11-004` | Volume/Turnover Confirmation | 20d | 5d | Winner: R_i_20 in Top Tercile AND VolumeRatio_i > 1.2. Loser: R_i_20 in Bottom Tercile AND VolumeRatio_i > 1.2. | Price momentum accompanied by abnormal turnover reflects institutional conviction and sustained order flow rather than thin-volume drift. |
| `H11-005` | Relative Strength Persistence | 60d | 10d | Sort eligible constituents by Score_i in descending order | Stocks that demonstrate consistent relative outperformance against the market across both short (20d) and medium (60d) horizons reflect durable multi-horizon strength. |
| `H11-006` | Market-Breadth Conditioning | 50d | 5d | Conditioned on aggregate breadth > 50%; within qualifying dates, sort by R_i_20 descending | Cross-sectional momentum operates effectively during constructive market breadth expansions, but experiences severe crashes during breadth deterioration. |

## Invariant Rule
No parameters, thresholds, or ranking rules may be altered after empirical calculation begins.
