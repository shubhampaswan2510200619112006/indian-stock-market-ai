# Intraday Benchmark Data Acceptance Report

## 1. Scope & Thresholds
- **Underlyings**: NIFTY 50 and NIFTY BANK (Index)
- **Intervals**: 1-minute and 5-minute (evaluated independently)
- **Research Threshold**: $N \ge 250$ verified trading sessions (`PROJECT_RESEARCH_THRESHOLD`)
- **Session Boundaries**: 09:15–15:30 IST (Asia/Kolkata)

## 2. Independent Interval Evaluation
- **1-Minute Interval Status**: `BLOCKED`
  - Reason: Public Yahoo endpoint capped at 7 calendar days (~7 sessions). Commercial vendor quote pending.
- **5-Minute Interval Status**: `BLOCKED`
  - Reason: Public Yahoo endpoint capped at 60 calendar days (~43 sessions). Fails 250-session threshold.
- **Auxiliary Data Note**: 1-hour data reaching >700 sessions is classified as `AUXILIARY_DATASET` and strictly cannot substitute for 1m/5m requirements.
