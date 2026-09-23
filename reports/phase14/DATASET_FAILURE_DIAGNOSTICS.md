# Dataset Failure Diagnostics Report

## Metadata Header
```text
DIAGNOSTICS_POLICY=Machine-readable deterministic failure codes
CERTIFICATION_TIMESTAMP=2026-09-09T11:04:06.699912+00:00
```

## Diagnostics by Dataset

### Dataset: `YAHOO_PUBLIC_NIFTY_1M_SAMPLE`
- **Certified**: `False`
- **Quarantined**: `False` (N/A)
- **Failure Codes**: `LICENSE_RESTRICTED, INSUFFICIENT_SESSIONS`
- **Rejection Reasons**:
  - `License contains non-commercial or restricted redistribution terms`
  - `Historical coverage insufficient: observed 7 valid sessions, below project research threshold of 250 sessions.`

### Dataset: `YAHOO_PUBLIC_NIFTY_5M_SAMPLE`
- **Certified**: `False`
- **Quarantined**: `False` (N/A)
- **Failure Codes**: `LICENSE_RESTRICTED, INSUFFICIENT_SESSIONS`
- **Rejection Reasons**:
  - `License contains non-commercial or restricted redistribution terms`
  - `Historical coverage insufficient: observed 59 valid sessions, below project research threshold of 250 sessions.`

### Dataset: `NSE_BHAVCOPY_OPTIONS_LTP_SAMPLE`
- **Certified**: `False`
- **Quarantined**: `False` (N/A)
- **Failure Codes**: `TIMESTAMP_NOT_CHRONOLOGICAL, CONTINUOUS_EXECUTABLE_SURFACE_LOW`
- **Rejection Reasons**:
  - `Timestamps are not strictly monotonically increasing`
  - `Paired quote coverage (0.24%) fails continuous executable surface threshold of >=70.0%`
