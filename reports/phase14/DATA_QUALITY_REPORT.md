# Data Quality Scorecard Report

## Policy Declaration
```text
DATA_QUALITY_SCORE=DIAGNOSTIC_ONLY
POLICY=Quality scores summarize diagnostics but NEVER override hard certification gates.
CERTIFICATION_TIMESTAMP=2026-09-09T11:04:06.699912+00:00
```

## Scorecards

### Dataset: `YAHOO_PUBLIC_NIFTY_1M_SAMPLE`
- **Diagnostic Score**: `78.89 / 100.0`
- **Hard Gates Intact**: `False`
- **Certification Eligible by Hard Gates**: `False`
- **Dimensions Evaluated**:
  - **PROVENANCE**: `PASS` (Score: 100.0, HardGatePassed: True) — Source artifact: VERIFIED
  - **LICENSE**: `BLOCKED` (Score: 50.0, HardGatePassed: False) — Status: LICENSE_RESTRICTED
  - **SCHEMA**: `PASS` (Score: 100.0, HardGatePassed: True) — Required schema columns verified
  - **TIMESTAMP**: `PASS` (Score: 100.0, HardGatePassed: True) — Monotonic chronological IST timestamp integrity
  - **SESSION_COVERAGE**: `FAIL` (Score: 2.8, HardGatePassed: False) — Observed 7 valid sessions (target: >= 250)
  - **BAR_COMPLETENESS**: `PASS` (Score: 95.0, HardGatePassed: True) — Session bar completeness evaluated
  - **OHLC_INTEGRITY**: `PASS` (Score: 100.0, HardGatePassed: True) — Violations: 0
  - **HISTORICAL_DEPTH**: `DIAGNOSTIC` (Score: 20.0, HardGatePassed: True) — Depth level: NOT_APPLICABLE
  - **CROSS_INSTRUMENT_COVERAGE**: `PASS` (Score: 100.0, HardGatePassed: True) — Instrument scoped: NIFTY 1m
  - **OPTIONS_QUOTE_VALIDITY**: `PASS` (Score: 100.0, HardGatePassed: True) — Crossed market checks evaluated
  - **OPTIONS_EXECUTABLE_SURFACE**: `PASS` (Score: 100.0, HardGatePassed: True) — Continuous surface: 100.0% (target >= 70.0%)

### Dataset: `YAHOO_PUBLIC_NIFTY_5M_SAMPLE`
- **Diagnostic Score**: `80.78 / 100.0`
- **Hard Gates Intact**: `False`
- **Certification Eligible by Hard Gates**: `False`
- **Dimensions Evaluated**:
  - **PROVENANCE**: `PASS` (Score: 100.0, HardGatePassed: True) — Source artifact: VERIFIED
  - **LICENSE**: `BLOCKED` (Score: 50.0, HardGatePassed: False) — Status: LICENSE_RESTRICTED
  - **SCHEMA**: `PASS` (Score: 100.0, HardGatePassed: True) — Required schema columns verified
  - **TIMESTAMP**: `PASS` (Score: 100.0, HardGatePassed: True) — Monotonic chronological IST timestamp integrity
  - **SESSION_COVERAGE**: `FAIL` (Score: 23.6, HardGatePassed: False) — Observed 59 valid sessions (target: >= 250)
  - **BAR_COMPLETENESS**: `PASS` (Score: 95.0, HardGatePassed: True) — Session bar completeness evaluated
  - **OHLC_INTEGRITY**: `PASS` (Score: 100.0, HardGatePassed: True) — Violations: 0
  - **HISTORICAL_DEPTH**: `DIAGNOSTIC` (Score: 20.0, HardGatePassed: True) — Depth level: NOT_APPLICABLE
  - **CROSS_INSTRUMENT_COVERAGE**: `PASS` (Score: 100.0, HardGatePassed: True) — Instrument scoped: NIFTY 5m
  - **OPTIONS_QUOTE_VALIDITY**: `PASS` (Score: 100.0, HardGatePassed: True) — Crossed market checks evaluated
  - **OPTIONS_EXECUTABLE_SURFACE**: `PASS` (Score: 100.0, HardGatePassed: True) — Continuous surface: 100.0% (target >= 70.0%)

### Dataset: `NSE_BHAVCOPY_OPTIONS_LTP_SAMPLE`
- **Diagnostic Score**: `74.11 / 100.0`
- **Hard Gates Intact**: `False`
- **Certification Eligible by Hard Gates**: `False`
- **Dimensions Evaluated**:
  - **PROVENANCE**: `PASS` (Score: 100.0, HardGatePassed: True) — Source artifact: VERIFIED
  - **LICENSE**: `PASS` (Score: 100.0, HardGatePassed: True) — Status: LICENSE_VERIFIED
  - **SCHEMA**: `PASS` (Score: 100.0, HardGatePassed: True) — Required schema columns verified
  - **TIMESTAMP**: `PASS` (Score: 100.0, HardGatePassed: True) — Monotonic chronological IST timestamp integrity
  - **SESSION_COVERAGE**: `PASS` (Score: 100.0, HardGatePassed: True) — Observed 0 valid sessions (target: >= 250)
  - **BAR_COMPLETENESS**: `PASS` (Score: 95.0, HardGatePassed: True) — Session bar completeness evaluated
  - **OHLC_INTEGRITY**: `FAIL` (Score: 0.0, HardGatePassed: False) — Violations: 0
  - **HISTORICAL_DEPTH**: `DIAGNOSTIC` (Score: 20.0, HardGatePassed: True) — Depth level: THEORETICAL_DEPTH
  - **CROSS_INSTRUMENT_COVERAGE**: `PASS` (Score: 100.0, HardGatePassed: True) — Instrument scoped: NIFTY eod
  - **OPTIONS_QUOTE_VALIDITY**: `PASS` (Score: 100.0, HardGatePassed: True) — Crossed market checks evaluated
  - **OPTIONS_EXECUTABLE_SURFACE**: `FAIL` (Score: 0.24, HardGatePassed: False) — Continuous surface: 0.24% (target >= 70.0%)
