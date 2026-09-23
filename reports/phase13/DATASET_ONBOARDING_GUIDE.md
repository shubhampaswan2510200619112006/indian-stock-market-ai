# Dataset Onboarding & Ingestion Guide

This guide details the exact operational procedure for receiving, validating, and qualifying incoming market data.

## 1. Linear Onboarding Workflow
```text
1. File Reception (SFTP / Cloud S3 / Direct Delivery)
   ↓
2. Compute SHA256 Checksum & File Hash Verification
   ↓
3. Assign Dataset Category (PRODUCTION_DATA vs TEST_FIXTURES vs AUXILIARY)
   ↓
4. Execute Phase13DataValidator (11-Stage Automated Ingestion Pipeline)
   ↓
5. Evaluate Dataset Scope (NIFTY vs BANKNIFTY, 1m vs 5m)
   ↓
6. Immutable Content-Based Versioning Registration (DatasetRegistry)
   ↓
7. Dynamic Readiness Gate Recalculation (Phase13ReadinessEngine)
```

## 2. Test Fixture Isolation Rules
- Test fixtures (`PIT_LEAK_TEST`, `TEST_CSV`) must NEVER be categorized as `PRODUCTION_DATA`.
- Any presence of synthetic or mock records in a production dataset automatically triggers `DATA_INTEGRITY = FAILED`.
