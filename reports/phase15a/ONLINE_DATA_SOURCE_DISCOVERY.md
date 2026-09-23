# ONLINE HISTORICAL DATA DISCOVERY & PUBLIC ACQUISITION REPORT

**Generated:** 2026-09-09 11:25:03 UTC  
**Evaluation Scope:** Legitimate online and public historical market data for Indian markets  
**Broker Connectivity:** `NONE` | **Live/Paper Execution:** `DISABLED` | **Payment Authorized:** `FALSE`  
**Phase 15 Unlocked:** `FALSE` | **Human Decision Required:** `TRUE`  

---

## 1. EXECUTIVE SUMMARY & EMPIRICAL FINDINGS

This investigation evaluated whether the platform's required historical research datasets (NIFTY/BANKNIFTY 1m, 5m, and Options with Bid/Ask/Depth) can be obtained from legitimate online public sources **without purchasing anything**.

### Authoritative Key Findings:
1. **Public Free Intraday Data (Yahoo Finance)**:
   - **NIFTY 1-minute**: Publicly accessible via Chart API, but strictly restricted by Yahoo to **rolling 7 calendar days maximum** (~5-7 sessions). Attempting queries beyond 7 days returns `HTTP 422: Unprocessable Entity`.
   - **NIFTY 5-minute**: Publicly accessible, but strictly restricted to **rolling 60 calendar days maximum** (~40 sessions). Range beyond 60 days returns `HTTP 422: Unprocessable Entity`.
   - **Qualification Verdict**: Both fail Phase 14 certification gate (`Valid sessions observed below required minimum threshold of 250 sessions`).
2. **Public Free Exchange Data (Official NSE Archives)**:
   - **NSE Bhavcopy**: Freely downloadable for multi-decade historical periods (`archives.nseindia.com`).
   - **Interval**: Strictly **Daily End-of-Day (1d)**.
   - **Options Quotes in Bhavcopy**: Provides Open, High, Low, Close, Settle Price, Contracts, Value, Open Interest.
   - **Bid / Ask / Market Depth**: **COMPLETELY ABSENT**. NSE Bhavcopy does NOT record Bid, Ask, or order-book depth.
   - **Qualification Verdict**: Fails Phase 14 continuous executable options surface certification (`OPTIONS_BID_MISSING`, `OPTIONS_ASK_MISSING`).
3. **Genuine Historical Options Bid/Ask & Tick Data**:
   - Genuinely available **ONLY as a commercial product** via **NSE Data & Analytics** or authorized commercial data vendors (**TrueData**, **Global Datafeeds**).
   - No legitimate, public, unauthenticated, redistribution-licensed source provides multi-year 1m/5m historical index data or historical options Bid/Ask for Indian exchanges without commercial payment.

---

## 2. EVALUATED SOURCES CATALOG

| Source Name | Category | Available Instruments | Max Interval / Range | Bid/Ask Available | Cost / Access | Authoritative Status |
|---|---|---|---|---|---|---|
| **NSE Official Derivatives Bhavcopy** | Official Exchange | Index & Stock Options | 1d (Daily EOD) / 2000-present | NO | Free / Public | `VERIFIED_PUBLIC` |
| **NSE Official Equities Bhavcopy** | Official Exchange | Cash Equities | 1d (Daily EOD) / 1994-present | NO | Free / Public | `VERIFIED_PUBLIC` |
| **Yahoo Finance NIFTY 1m** | Aggregator API | NIFTY 50 Index | 1m / 7 Days max | NO | Free / Public | `VERIFIED_PUBLIC` |
| **Yahoo Finance NIFTY 5m** | Aggregator API | NIFTY 50 Index | 5m / 60 Days max | NO | Free / Public | `VERIFIED_PUBLIC` |
| **Yahoo Finance Options** | Aggregator API | None for NSE | None | NO | N/A | `UNAVAILABLE` |
| **NSE Data & Analytics (InfoSys)** | Exchange Commercial | NIFTY, BANKNIFTY, Options | 1m, 5m, Tick / 2014-present | YES | Paid License | `VERIFIED_COMMERCIAL` |
| **TrueData Historical** | Authorized Vendor | NIFTY, BANKNIFTY, Options | 1m, 5m, Tick / 10+ Years | YES (Tick) | Paid Subscription | `VERIFIED_COMMERCIAL` |
| **Global Datafeeds (GDFL)** | Authorized Vendor | NIFTY, BANKNIFTY, Options | 1m, 5m, Tick / 2015-present | YES | Paid Subscription | `VERIFIED_COMMERCIAL` |
| **Google Finance** | Web Portal | Daily Charts | 1d / View-only | NO | View-only | `UNAVAILABLE` |
| **Kaggle Community Uploads** | Community Upload | NIFTY 1m (Unverified) | Fragmented user scraps | NO | Auth required | `VENDOR_CLAIM` |

---

## 3. PUBLIC DATASETS DOWNLOADED & PHASE 15A INTAKE AUDIT

Three genuine public datasets were downloaded, cataloged in `data/intake/raw/`, cryptographically hashed, normalized, and handed off to Phase 14 certification:

### Dataset: `NIFTY50_1M_YAHOO_7D`
- **Intake ID:** `INTAKE-PUB-YAHOO-NIFTY-1M`
- **Raw File:** `data/intake\raw\yahoo_nifty50_1m_7d_raw.csv`
- **Raw SHA256:** `56e69b5b8fe6e7b5eebe4a77738c7dc1189f40b6b27b0ea2e0d687bf7dae063d`
- **Normalized File:** `data/intake\normalized\nifty50_1m_yahoo_7d_normalized.csv`
- **Normalized SHA256:** `c60375376ba84bb357c88a52204fcfe3c64ffa28f08753b70e7ed539df9a0802`
- **Total Records:** 2,626
- **Lifecycle Final State:** `CERTIFICATION_FAILED`
- **Phase 14 Qualification Outcome:** `CERTIFICATION_FAILED`
- **Rejection Reasons:**
  - `Historical coverage insufficient: observed 7 valid sessions, below project research threshold of 250 sessions.`

### Dataset: `BANKNIFTY_1M_YAHOO_7D`
- **Intake ID:** `INTAKE-PUB-YAHOO-BANKNIFTY-1M`
- **Raw File:** `data/intake\raw\yahoo_banknifty_1m_7d_raw.csv`
- **Raw SHA256:** `23a64f19c74bcff24d295ba5d1882fb2f7ebe2d9361bfd4b67a148463d4ba339`
- **Normalized File:** `data/intake\normalized\banknifty_1m_yahoo_7d_normalized.csv`
- **Normalized SHA256:** `a1e6b849c29aff1e0c3f05b566465136a82aa21d5b719153532e14ced8818fa9`
- **Total Records:** 2,626
- **Lifecycle Final State:** `CERTIFICATION_FAILED`
- **Phase 14 Qualification Outcome:** `CERTIFICATION_FAILED`
- **Rejection Reasons:**
  - `Historical coverage insufficient: observed 7 valid sessions, below project research threshold of 250 sessions.`

### Dataset: `NSE_FO_BHAVCOPY_20240101`
- **Intake ID:** `INTAKE-PUB-NSE-BHAVCOPY-FO`
- **Raw File:** `data/intake\raw\nse_fo_01JAN2024bhav_raw.csv.zip`
- **Raw SHA256:** `c79a51fed3a632f23650ffb3907889433565ff669ced06a47bc61ca739b1f979`
- **Normalized File:** `data/intake\normalized\nse_fo_01JAN2024bhav_normalized.csv`
- **Normalized SHA256:** `49a17ae776d17e1e151b9959ce8190945b9f6fbf162887da29845495437d8525`
- **Total Records:** 56,662
- **Lifecycle Final State:** `CERTIFICATION_FAILED`
- **Phase 14 Qualification Outcome:** `CERTIFICATION_FAILED`
- **Rejection Reasons:**
  - `Observed 89641 OHLC geometric violations or zero/negative prices`
  - `Options quotes lack valid Bid prices`
  - `Options quotes lack valid Ask prices`
  - `Paired quote coverage (0.0%) fails continuous executable surface threshold of >=70.0%`

---

## 4. GAP ANALYSIS: UNMET RESEARCH REQUIREMENTS

| Required Data Capability | Best Publicly Downloadable Source | Public Data Limitation | Commercial Solution | Current Status |
|---|---|---|---|---|
| **NIFTY 1m (>=250 sessions)** | Yahoo Finance (7 days / 2,626 bars) | Strictly capped at 7 days by Yahoo (~5 sessions) | NSE Data & Analytics / TrueData | **BLOCKED (INSUFFICIENT HISTORY)** |
| **NIFTY 5m (>=250 sessions)** | Yahoo Finance (60 days / 4,501 bars) | Strictly capped at 60 days (~40 sessions) | NSE Data & Analytics / TrueData | **BLOCKED (INSUFFICIENT HISTORY)** |
| **BANKNIFTY 1m (>=250 sessions)** | Yahoo Finance (7 days / 2,626 bars) | Strictly capped at 7 days by Yahoo (~5 sessions) | NSE Data & Analytics / TrueData | **BLOCKED (INSUFFICIENT HISTORY)** |
| **Options Historical LTP** | NSE Official F&O Bhavcopy | Available Daily EOD only (No intraday timestamps) | NSE Data & Analytics / TrueData | **PASS (DAILY ONLY) / BLOCKED (INTRADAY)** |
| **Options Historical Bid/Ask** | NONE | Absent from all public/free sources | NSE Data & Analytics / TrueData / GDFL | **BLOCKED (COMMERCIAL ONLY)** |
| **Options Order Book Depth** | NONE | Absent from all public/free sources | NSE Data & Analytics (L2/L3) | **BLOCKED (COMMERCIAL ONLY)** |

---

## 5. FINAL READINESS CONCLUSION

1. **Intraday Research Capability:** **BLOCKED**
   - Public 1-minute and 5-minute sources do not provide sufficient historical depth (7 days to 60 days, far below the required 250 trading sessions).
2. **Options Execution Research Capability:** **BLOCKED**
   - Genuine historical Bid/Ask prices and continuous executable surface data do not exist in any legitimate public, unauthenticated, non-commercial domain.
3. **Overall Platform Readiness:** **BLOCKED**
   - Free public sources cannot satisfy the preregistered research requirements.
   - Legitimate acquisition requires commercial data procurement, which is strictly locked under `PURCHASE_AUTHORIZED=FALSE` awaiting formal human acquisition decision.
4. **Safety Compliance:**
   - Zero live trading, zero automated purchasing, zero broker connections, and zero unpreregistered alpha research have occurred.
   - Phase 15 research remains **STRICTLY LOCKED**.
