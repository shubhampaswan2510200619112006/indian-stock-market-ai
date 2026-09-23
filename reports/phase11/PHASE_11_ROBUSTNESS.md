# Phase 11: Robustness Report

## Transaction Cost Stress Testing

| Hypothesis ID | 1.0x Baseline Net Exp | 1.5x Stress Net Exp | 2.0x Stress Net Exp | Survives Cost Stress? |
| :--- | :---: | :---: | :---: | :---: |
| `H11-001` | -65.25 bps | -73.79 bps | -82.33 bps | `NO` |
| `H11-002` | -29.88 bps | -38.42 bps | -46.96 bps | `NO` |
| `H11-003` | -59.28 bps | -67.82 bps | -76.36 bps | `NO` |
| `H11-004` | -83.50 bps | -87.26 bps | -91.03 bps | `NO` |
| `H11-005` | -43.56 bps | -52.10 bps | -60.64 bps | `NO` |
| `H11-006` | -35.49 bps | -38.34 bps | -41.19 bps | `NO` |

## Partition Stability (Train vs Validation vs Untouched OOS)

| Hypothesis ID | Train Net Exp (bps) | Val Net Exp (bps) | OOS Net Exp (bps) | Sign Consistency |
| :--- | :---: | :---: | :---: | :---: |
| `H11-001` | -57.62 | -85.61 | -65.25 | `CONSISTENT` |
| `H11-002` | +5.52 | -16.60 | -29.88 | `INCONSISTENT` |
| `H11-003` | -65.52 | -62.51 | -59.28 | `CONSISTENT` |
| `H11-004` | -51.71 | -0.85 | -83.50 | `CONSISTENT` |
| `H11-005` | -58.27 | -130.23 | -43.56 | `CONSISTENT` |
| `H11-006` | -20.75 | -75.95 | -35.49 | `CONSISTENT` |