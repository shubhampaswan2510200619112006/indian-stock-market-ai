# Market Data Acquisition Decision Tree

```mermaid
graph TD
    Start([Candidate Evaluation]) --> IntradayCheck{Satisfies Intraday Coverage?<br/>N >= 250 sessions 1m/5m}
    IntradayCheck -- NO --> RejectIntraday[Reject for Intraday Research Track]
    IntradayCheck -- YES --> OptionsCheck{Satisfies Options Bid/Ask?<br/>Paired quotes, expired contracts}
    OptionsCheck -- NO --> RejectOptions[Reject for Options Execution Track<br/>Accept for Intraday Only if approved]
    OptionsCheck -- YES --> EvidenceCheck{Evidence Independently Verified?<br/>Sample dataset passes 11-stage audit}
    EvidenceCheck -- NO --> SampleValidation[Hold in SAMPLE_VALIDATION_PENDING<br/>Request formal sample dataset]
    EvidenceCheck -- YES --> LicenseCheck{Commercial License Suitable?<br/>Proprietary research permitted}
    LicenseCheck -- NO --> RejectLicense[Reject on Legal / Licensing Grounds]
    LicenseCheck -- YES --> CommercialCheck{Formal Commercial Quote Acceptable?<br/>Transparent pricing + budget fit}
    CommercialCheck -- NO --> Negotiate[Commercial Negotiation / Hold in COMMERCIAL_REVIEW_PENDING]
    CommercialCheck -- YES --> HumanGate{Explicit Human Authorization Signed?<br/>HUMAN_DECISION_REQUIRED}
    HumanGate -- NO --> Stop[STOP: No purchase authorized. Hold in HUMAN_AUTHORIZATION_PENDING]
    HumanGate -- YES --> Proceed[APPROVED_FOR_ACQUISITION: Proceed to Human Procurement]
```

## Strict Decision Rules
1. **Zero Automated Purchasing**: Under no circumstances may an automated process transition state to `APPROVED_FOR_ACQUISITION` or trigger payment.
2. **Zero Research Unlock**: Ingesting acquired data does NOT automatically activate live or paper alpha research.
3. **Hard Gate Non-Override**: Cost scores cannot override missing technical capabilities.
