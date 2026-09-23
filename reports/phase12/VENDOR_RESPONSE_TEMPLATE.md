# Market Data Vendor Response Capture Template

Use this structured template to record every vendor response received from sales or technical inquiries.

```text
provider: [Vendor Name, e.g. TrueData, NSE Data & Analytics]
contact: [Sales representative name, email, phone]
date_received: [YYYY-MM-DD]
product_name: [Exact official product name]
dataset: [e.g. Intraday 1m/5m Index, Options 5-Depth TBT]
date_range: [Available start date to end date]
coverage: [Symbols, segments, sessions covered]
granularity: [1-minute, 5-minute, tick, second snapshot]
quote_type: [OHLCV bar, Top-of-Book BBO, 5-depth, full order book]
depth: [None, 5-depth, 20-depth, Full L3]
contract_coverage: [All strikes / All expiries / Expired contracts included?]
timestamp_standard: [Exchange microsecond, vendor millisecond, IST offset]
format: [CSV, Parquet, JSON, binary PCAP]
delivery_method: [REST API, WebSocket, SFTP, AWS S3, External HDD]
license: [Internal quantitative research / Non-display / Commercial redistribution prohibited]
one_time_cost: [INR / USD amount, or NONE]
recurring_cost: [INR / USD per month or year]
taxes: [18% GST included or excluded]
exchange_fees: [Included in vendor price or billed separately by exchange]
other_fees: [Setup fees, API key fee, maintenance fee]
support: [Email, telephone, SLA response time]
SLA: [Uptime guarantee, revision notification timeline]
limitations: [Observed or stated vendor limitations]
evidence: [Attached sample file, contract draft, technical documentation URL]
vendor_confirmation_status: [CONFIRMED / PENDING_CLARIFICATION / REJECTED]
```
