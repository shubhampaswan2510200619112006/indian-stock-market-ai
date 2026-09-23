# Options Microstructure Acceptance Report

## 1. Options Executability Hierarchy
- **Level 0 (No Data)**: Completely unrecorded.
- **Level 1 (LTP / Settlement Only)**: `PASS` (Bhavcopy settlement data verified).
- **Level 2 (Isolated Bid/Ask)**: `BLOCKED` (Requires empirical paired quote observations).
- **Level 3 (Continuous Paired Surface)**: `BLOCKED` (Requires $\ge 70.0\%$ paired quote continuity across trading hours).
- **Level 4 (Depth / Order Book Reconstructable)**: `BLOCKED` (Requires enterprise order log archives).

## 2. Strict Continuous Surface Metric Definition
- Evaluated strictly during legitimate trading hours when the option contract was active and listed.
- Periods prior to contract introduction or following contract expiry are not counted as missing data.
- Crossed quotes (`bid > ask`) and non-positive quotes are disqualified from executable surface calculations.
