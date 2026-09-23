# Full Dataset Certification Report

## Metadata Header
```text
VALIDATION_VERSION=cert_v1
CALENDAR_VERSION=nse_cal_v1
SCHEMA_VERSION=phase14_v1
CERTIFICATION_TIMESTAMP=2026-09-09T11:04:06.699912+00:00
```

## Evaluated Datasets

### Dataset: `YAHOO_PUBLIC_NIFTY_1M_SAMPLE` (v1)
- **Vendor**: `Yahoo Finance`
- **Underlying / Interval**: `NIFTY` `1m`
- **Certified**: `False`
- **License Status**: `LICENSE_RESTRICTED`
- **Provenance Status**: `VERIFIED`
- **Stages Passed**: `0. FIXTURE QUARANTINE, 1. IDENTITY, 2. PROVENANCE, 4. SCHEMA, 5. TIMESTAMP, 6. OHLC INTEGRITY, 7. SESSION COMPLETENESS`
- **Stages Failed**: `3. LICENSE, 8. HISTORICAL COVERAGE`
- **Rejection Reasons**: `License contains non-commercial or restricted redistribution terms; Historical coverage insufficient: observed 7 valid sessions, below project research threshold of 250 sessions.`

### Dataset: `YAHOO_PUBLIC_NIFTY_5M_SAMPLE` (v1)
- **Vendor**: `Yahoo Finance`
- **Underlying / Interval**: `NIFTY` `5m`
- **Certified**: `False`
- **License Status**: `LICENSE_RESTRICTED`
- **Provenance Status**: `VERIFIED`
- **Stages Passed**: `0. FIXTURE QUARANTINE, 1. IDENTITY, 2. PROVENANCE, 4. SCHEMA, 5. TIMESTAMP, 6. OHLC INTEGRITY, 7. SESSION COMPLETENESS`
- **Stages Failed**: `3. LICENSE, 8. HISTORICAL COVERAGE`
- **Rejection Reasons**: `License contains non-commercial or restricted redistribution terms; Historical coverage insufficient: observed 59 valid sessions, below project research threshold of 250 sessions.`

### Dataset: `NSE_BHAVCOPY_OPTIONS_LTP_SAMPLE` (v1)
- **Vendor**: `NSE Public Web`
- **Underlying / Interval**: `NIFTY` `eod`
- **Certified**: `False`
- **License Status**: `LICENSE_VERIFIED`
- **Provenance Status**: `VERIFIED`
- **Stages Passed**: `0. FIXTURE QUARANTINE, 1. IDENTITY, 2. PROVENANCE, 3. LICENSE, 4. SCHEMA, 5. TIMESTAMP, 10. OPTIONS CONTRACT INTEGRITY`
- **Stages Failed**: `11. OPTIONS CONTINUITY`
- **Rejection Reasons**: `Timestamps are not strictly monotonically increasing; Paired quote coverage (0.24%) fails continuous executable surface threshold of >=70.0%`
