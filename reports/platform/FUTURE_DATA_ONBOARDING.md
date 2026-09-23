# Future Data Onboarding & Ingestion Guide

## Automated 11-Stage Ingestion Pipeline
Any incoming dataset from an approved vendor (e.g. TrueData, NSE Data & Analytics) must pass through `DataArrivalValidator` before capabilities are unlocked:

```text
Stage 1: INGEST ────────────────── Verify non-null payload & row counts
Stage 2: SCHEMA VALIDATION ─────── Enforce required field names and types
Stage 3: TIMESTAMP VALIDATION ──── Parse ISO-8601 timestamps and verify monotonicity
Stage 4: DUPLICATE CHECK ───────── Detect and reject duplicate contract/timestamp keys
Stage 5: OHLC VALIDATION ───────── Logical high >= low, high >= open/close checks
Stage 6: CORPORATE ACTION ──────── Adjust splits and dividend distributions
Stage 7: CONTRACT VALIDATION ───── Verify CE/PE options contracts and expiries
Stage 8: BID/ASK VALIDATION ────── Evaluate paired quote rules (Bid > 0, Ask >= Bid)
Stage 9: COVERAGE ANALYSIS ─────── Audit unique session counts against thresholds
Stage 10: PROVENANCE RECORDING ─── Document vendor, source URL, and cryptographic hash
Stage 11: READINESS GATE ───────── Formally unlock capability if criteria are met
```

## Options Quality Hierarchy (L0 to L4)
- **Level 0 (L0)**: No historical executable quote evidence (LTP or settlement only).
- **Level 1 (L1)**: Bid and Ask columns exist in schema.
- **Level 2 (L2)**: Valid paired observations (`Bid > 0, Ask > 0, Ask >= Bid` at identical timestamp).
- **Level 3 (L3)**: Sufficiently continuous timestamped executable surface across trading hours and strikes (>= 70% coverage).
- **Level 4 (L4)**: Independently audited and verified research-grade historical execution dataset.

## Zero-Credential Ingestion Standard
Credentials must NEVER be committed to source code. Data onboarding accepts pre-downloaded local Parquet/CSV files or environment-configured secure S3 paths.
