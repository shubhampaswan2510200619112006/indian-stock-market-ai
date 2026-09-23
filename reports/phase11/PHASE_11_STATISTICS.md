# Phase 11: Statistical & Multiplicity Control Report

## Multiplicity Control Summary
- **Total Primary Hypotheses**: 6
- **Nominal Significance Alpha**: 0.05
- **Bonferroni FWER Threshold**: 0.00833
- **Bonferroni Surviving Candidates**: 0
- **Benjamini-Hochberg Surviving Candidates**: 0
- **Verdict Statement**: `NO_STATISTICAL_CLAIM_SURVIVED_MULTIPLICITY_ADJUSTMENT`

## Stationary Block Bootstrap (1,000 Resamples, Seed=42, Block Length=5)

| Hypothesis ID | OOS Net Exp | 95% Bootstrap CI (bps) | Sharpe Mean | 95% Sharpe CI | Bootstrap p-value | Multiplicity Result |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `H11-001` | -65.25 bps | [-156.67, +33.95] | -1.66 | [-4.27, +0.63] | 0.8970 | `NOT_SIGNIFICANT` |
| `H11-002` | -29.88 bps | [-98.70, +39.38] | -0.71 | [-2.44, +0.85] | 0.8150 | `NOT_SIGNIFICANT` |
| `H11-003` | -59.28 bps | [-144.81, +41.36] | -1.65 | [-4.22, +0.74] | 0.8860 | `NOT_SIGNIFICANT` |
| `H11-004` | -83.50 bps | [-190.46, +28.81] | -1.95 | [-4.45, +0.71] | 0.9360 | `NOT_SIGNIFICANT` |
| `H11-005` | -43.56 bps | [-179.63, +121.79] | -0.58 | [-2.75, +0.98] | 0.7250 | `NOT_SIGNIFICANT` |
| `H11-006` | -35.49 bps | [-67.95, -3.86] | -1.76 | [-2.84, -0.51] | 0.9860 | `NOT_SIGNIFICANT` |

## Block Length Sensitivity Checks

| Hypothesis ID | Block Length 3 CI (bps) | Block Length 5 CI (bps) | Block Length 10 CI (bps) |
| :--- | :---: | :---: | :---: |
| `H11-001` | [-161.33, +42.08] | [-156.67, +33.95] | [-149.37, +25.95] |
| `H11-002` | [-110.09, +57.62] | [-98.70, +39.38] | [-86.26, +27.10] |
| `H11-003` | [-147.95, +44.03] | [-144.81, +41.36] | [-141.57, +33.89] |
| `H11-004` | [-198.65, +22.73] | [-190.46, +28.81] | [-182.80, +18.50] |
| `H11-005` | [-183.34, +129.68] | [-179.63, +121.79] | [-164.94, +77.20] |
| `H11-006` | [-67.89, -5.80] | [-67.95, -3.86] | [-65.73, -5.80] |