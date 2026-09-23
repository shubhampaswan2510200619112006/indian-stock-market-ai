# Phase 12 — Final Vendor Contact & Data Acquisition Decision Package

> [!IMPORTANT]
> **ABSOLUTE GOVERNANCE INVARIANT**:
> `PURCHASE_AUTHORIZED = FALSE`
> `HUMAN_DECISION_REQUIRED = TRUE`
> `BROKER = NONE`
> `LIVE_EXECUTION = DISABLED`
> `AUTO_PAPER_ORDER_SUBMISSION = DISABLED`
> `NEW_UNPREREGISTERED_ALPHA_RESEARCH = DISABLED`
> `OPTIONS_EXECUTION = BLOCKED`
> `FROZEN_BASELINES = INTACT`
>
> This document is a **decision and vendor inquiry package**, NOT an acquisition. Zero purchases, zero broker connections, and zero alpha research activations have occurred.

## 1. Executive Summary
The platform has completed all empirical evaluations across Phases 9.7 through 12. Research demonstrates that while Daily EOD equity data and Options Bhavcopy LTP settlement data are fully ready, intraday and options execution research tracks remain blocked due to empirical data boundaries:
1. **Intraday 1m/5m Benchmark Data**: Public endpoints retain only 7 days (1m) and 60 days (5m), failing the project threshold of $N \ge 250$ verified sessions.
2. **Options Execution Microstructure**: Existing Bhavcopy records provide settlement LTP only ($99.34\%$ settlement coverage, $0.0\%$ continuous paired quote surface), preventing realistic slippage and friction simulation.

This package arms human operators with complete, copy-ready vendor inquiry emails, questionnaires, evaluation matrices, cost models, pre-purchase validation criteria, and a human approval form.

## 2. Current Platform State
```text
DAILY_DATA_READY               = PASS
CROSS_SECTIONAL_DATA_READY     = PASS
INTRADAY_1M_READY              = BLOCKED
INTRADAY_5M_READY              = BLOCKED
OPTIONS_LTP_READY              = PASS
OPTIONS_BID_ASK_READY          = BLOCKED
OPTIONS_EXECUTION_READY        = BLOCKED
PURCHASE_AUTHORIZED            = FALSE
HUMAN_DECISION_REQUIRED        = TRUE
BROKER                         = NONE
LIVE_EXECUTION                 = DISABLED
AUTO_PAPER_ORDER_SUBMISSION    = DISABLED
NEW_ALPHA_RESEARCH             = DISABLED
FROZEN_BASELINES               = INTACT
OVERALL_STATE                  = AWAITING_HUMAN_VENDOR_DECISION
```

## 3. Exact Data Gap
- **Intraday Gap**: Need multi-year 1m and 5m continuous bars for NIFTY 50 and NIFTY BANK covering $\ge 250$ trading sessions (preferred 3–5 years).
- **Options Microstructure Gap**: Need historical timestamped paired Bid/Ask quote surfaces (Level 2 5-depth or Level 3/4 order book) covering active and expired contracts with $\ge 70\%$ paired quote continuity across trading hours.

## 4. Exact Acquisition Requirements
Specifications are formalized in `data/phase12/acquisition_decision_package.json`:
- Underlyings: NIFTY 50, NIFTY BANK (Index), NIFTY / BANKNIFTY Options.
- Sessions: $\ge 250$ verified sessions labeled `PROJECT_RESEARCH_THRESHOLD`.
- Continuity: $\ge 70.0\%$ paired quote coverage labeled `PROJECT_RESEARCH_THRESHOLD`.
- Contract Expiry: Dynamic exchange specification and holiday calendar driven (hardcoded weekdays forbidden).

## 5. Provider Comparison & Provisional Ranking
```text
PROVISIONAL_CANDIDATE_RANKING
SUBJECT_TO_VENDOR_CONFIRMATION
SUBJECT_TO_FORMAL_QUOTATION
SUBJECT_TO_LICENSE_REVIEW
SUBJECT_TO_SAMPLE_VALIDATION

PREFERRED CANDIDATE: NSE Data & Analytics Ltd (DotEx)
SECONDARY CANDIDATE: TrueData (TrueData India)
BACKUP CANDIDATE:    Global DataFeeds (GDFL)
DISQUALIFIED:        Zerodha, Upstox, Angel One, FYERS, Yahoo Finance
```
*Note: Ranking is provisional and does not constitute a purchase authorization.*

## 6. Evidence Quality & Discipline
All claims are backed by provenance in `data/phase12/vendor_claims.json`:
- **VERIFIED**: Supported by authoritative documentation or empirical testing.
- **REQUIRES_VENDOR_CONFIRMATION**: Plausible capability requiring sample audit.
- **ESTIMATE — NOT A QUOTE**: Non-binding estimated pricing.
- **VERIFIED_QUOTE**: Confirmed binding quote.
- **NOT_AVAILABLE**: Capability confirmed absent.
- **OBSERVED_PROVIDER_LIMITATION**: Empirically observed boundary.

## 7. Unknowns Requiring Vendor Confirmation
1. **TrueData / GDFL**: Whether historical options tick archives contain continuous paired Bid/Ask for expired contracts, or merely bar OHLCV.
2. **NSE DotEx**: Exact commercial quotation and format specifications for historical Level 2 5-depth snapshots.
3. **Licensing**: Formal confirmation that internal non-display quantitative research is permitted without ongoing distribution fees.

## 8. Cost Comparison Model
Details recorded in `data/phase12/cost_comparison.json`:
- **NSE DotEx**: `REQUIRES_VENDOR_QUOTE` (Estimated INR 50k - 250k+; marked `ESTIMATE — NOT A QUOTE`).
- **TrueData**: `ESTIMATE — NOT A QUOTE` (Estimated INR 25k - 60k/yr + 18% GST).
- **GDFL**: `ESTIMATE — NOT A QUOTE` (Estimated INR 20k - 50k/yr + 18% GST).
- **Zerodha**: `VERIFIED_QUOTE` (INR 48,000/yr), but disqualified due to lack of options Bid/Ask and contract pruning.

## 9. Licensing Considerations
- Must guarantee internal quantitative analysis and strategy simulation rights.
- Must confirm permanent internal retention of derived models, signals, and backtest results.
- Redistribution to external parties is prohibited.

## 10. Vendor Questions
Full 20 intraday questions and 30 options microstructure questions documented in `reports/phase12/VENDOR_CONTACT_QUESTIONNAIRE.md`.

## 11. Pre-Purchase Validation Procedure
Candidate sample datasets must pass the 11-stage `DataOnboardingValidator` detailed in `reports/phase12/PRE_PURCHASE_ACCEPTANCE_TEST.md` prior to contract execution.

## 12. Decision Tree
Logical gate progression documented in `reports/phase12/ACQUISITION_DECISION_TREE.md`.

## 13. Human Decision Form
Formal sign-off form ready for human signature in `reports/phase12/HUMAN_ACQUISITION_DECISION_FORM.md`.

## 14. Recommended Contact Order
1. **First Contact**: Send `reports/phase12/VENDOR_ENQUIRY_NSE.md` to NSE Data & Analytics.
2. **Parallel Contact**: Send `reports/phase12/VENDOR_ENQUIRY_TRUEDATA.md` to TrueData.
3. **Parallel Contact**: Send `reports/phase12/VENDOR_ENQUIRY_GDFL.md` to Global DataFeeds.
4. **Response Capture**: Log all responses into `reports/phase12/VENDOR_RESPONSE_TEMPLATE.md` and `data/phase12/vendor_responses.json`.
5. **Sample Audit**: Validate sample datasets via `PRE_PURCHASE_ACCEPTANCE_TEST.md`.
6. **Human Decision**: Present completed matrix and form to human decision maker.

## 15. Explicit Statement: No Purchase Has Been Authorized
> [!WARNING]
> Zero commercial purchases have been authorized. `PURCHASE_AUTHORIZED = FALSE`. No accounts, payments, or contracts have been entered into.

## 16. Explicit Statement: No Research Has Been Unlocked
> [!CAUTION]
> No alpha research, strategy optimization, parameter searches, broker connections, live trading, or paper trading have been unlocked. All research gates remain frozen.

## 17. Final State Summary
```text
PHASE_12_ACQUISITION_PACKAGE = COMPLETE
VENDOR_CONTACT_PACKAGE = READY
PRE_PURCHASE_VALIDATION = READY
COST_COMPARISON = READY
HUMAN_DECISION_FORM = READY

INTRADAY_1M_READY = BLOCKED
INTRADAY_5M_READY = BLOCKED
OPTIONS_BID_ASK_READY = BLOCKED
OPTIONS_EXECUTION_READY = BLOCKED

PURCHASE_AUTHORIZED = FALSE
HUMAN_DECISION_REQUIRED = TRUE

BROKER = NONE
LIVE_EXECUTION = DISABLED
AUTO_PAPER_ORDER_SUBMISSION = DISABLED

NEW_UNPREREGISTERED_ALPHA_RESEARCH = DISABLED

FROZEN_BASELINES = INTACT

OVERALL_STATE = AWAITING_HUMAN_VENDOR_DECISION
```
