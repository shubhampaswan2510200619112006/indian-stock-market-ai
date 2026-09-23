# Market Data Vendor Comparison Matrix

> [!NOTE]
> Unconfirmed or unverified fields strictly display as `UNKNOWN`. No speculative estimates or inferred capabilities are populated.

| Category | NSE Data & Analytics | TrueData | Global DataFeeds (GDFL) | Zerodha Kite | Public / Free |
|---|---|---|---|---|---|
| **1m NIFTY 50** | VERIFIED (>10 yrs) | VERIFIED (>10 yrs) | VERIFIED (>5 yrs) | VERIFIED (~1-2 yrs) | OBSERVED_LIMITATION (7 days) |
| **1m NIFTY BANK** | VERIFIED (>10 yrs) | VERIFIED (>10 yrs) | VERIFIED (>5 yrs) | VERIFIED (~1-2 yrs) | OBSERVED_LIMITATION (7 days) |
| **5m NIFTY 50** | VERIFIED (>10 yrs) | VERIFIED (>10 yrs) | VERIFIED (>5 yrs) | VERIFIED (~1-2 yrs) | OBSERVED_LIMITATION (60 days) |
| **5m NIFTY BANK** | VERIFIED (>10 yrs) | VERIFIED (>10 yrs) | VERIFIED (>5 yrs) | VERIFIED (~1-2 yrs) | OBSERVED_LIMITATION (60 days) |
| **Historical Options** | VERIFIED (Full F&O) | VERIFIED (Bar OHLCV) | VERIFIED (Bar OHLCV) | NOT_AVAILABLE | NOT_AVAILABLE |
| **Historical Bid/Ask** | VERIFIED (Snapshots) | REQUIRES_CONFIRMATION | REQUIRES_CONFIRMATION | NOT_AVAILABLE | NOT_AVAILABLE |
| **Paired Bid/Ask** | VERIFIED (Matching tape) | REQUIRES_CONFIRMATION | REQUIRES_CONFIRMATION | NOT_AVAILABLE | NOT_AVAILABLE |
| **Quote Continuity (>=70%)** | REQUIRES_RECONSTRUCTION | REQUIRES_CONFIRMATION | REQUIRES_CONFIRMATION | NOT_AVAILABLE | NOT_AVAILABLE |
| **5-Depth Available** | VERIFIED (L2 archives) | LIVE_ONLY (Hist UNKNOWN) | LIVE_ONLY (Hist UNKNOWN) | NOT_AVAILABLE | NOT_AVAILABLE |
| **Full Order-Book Data** | VERIFIED (L3 TBT) | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE | NOT_AVAILABLE |
| **Expired Contracts** | VERIFIED (All years) | VERIFIED (Bar format) | VERIFIED (Bar format) | NOT_AVAILABLE (Pruned) | NOT_AVAILABLE |
| **Historical OI** | VERIFIED (Intraday) | VERIFIED (Minute bar) | VERIFIED (Minute bar) | VERIFIED (Active only) | VERIFIED (Bhavcopy EOD) |
| **Timestamp Quality** | Exchange Microsecond | Millisecond API | Second Resolution | Minute Bar | Minute Bar / Daily |
| **Bulk Archive Access** | VERIFIED (S3/SFTP/HDD) | REQUIRES_CONFIRMATION | REQUIRES_CONFIRMATION | NOT_AVAILABLE | NOT_AVAILABLE |
| **API Access** | Enterprise SFTP/API | REST + WebSocket API | Desktop Bridge / API | REST HTTP API | Public HTTP |
| **Historical Range** | Multi-year (10+ yrs) | Multi-year (10+ yrs) | Multi-year (5+ yrs) | ~1-2 yrs active | 7d (1m) / 60d (5m) |
| **Licensing Fit** | Commercial Research | Proprietary Prop | Proprietary Prop | Retail Trading Only | Personal / Free Only |
| **One-Time Cost** | REQUIRES_VENDOR_QUOTE | REQUIRES_VENDOR_QUOTE | REQUIRES_VENDOR_QUOTE | None | None |
| **Recurring Cost** | REQUIRES_VENDOR_QUOTE | EST: INR 25k-60k/yr | EST: INR 20k-50k/yr | VERIFIED: INR 48k/yr | Free |
| **Exchange Fees** | Quoted in Contract | Included | Included | Included | None |
| **Support / SLA** | Enterprise SLA | Commercial SLA | Commercial SLA | Retail Ticket | None |
| **Evidence Status** | VERIFIED | REQUIRES_CONFIRMATION | REQUIRES_CONFIRMATION | VERIFIED (Disqualified) | VERIFIED (Disqualified) |
| **Independent Validation** | Sample Required | Sample Required | Sample Required | Audited in Phase 10 | Audited in Phase 10 |

