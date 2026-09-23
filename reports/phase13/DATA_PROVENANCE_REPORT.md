# Data Provenance & Lineage Report

## 1. Provenance Inventory
Every registered dataset maintains an immutable cryptographic manifest:

| Dataset ID | Version | Category | Vendor | Underlying | Frequency | Records | Source Checksum | License Status |
|---|---|---|---|---|---|---|---|---|
| `YAHOO_PUBLIC_NIFTY_1M_SAMPLE` | `v1` | `AUXILIARY_DATASET` | `Yahoo Finance` | `NIFTY 50` | `1m` | 2625 | `sha256_publi...` | `LICENSE_RESTRICTED` |
| `YAHOO_PUBLIC_NIFTY_5M_SAMPLE` | `v1` | `AUXILIARY_DATASET` | `Yahoo Finance` | `NIFTY 50` | `5m` | 4425 | `sha256_publi...` | `LICENSE_RESTRICTED` |
| `NSE_BHAVCOPY_OPTIONS_LTP_SAMPLE` | `v1` | `PRODUCTION_DATA` | `NSE Public Web` | `NIFTY` | `eod` | 846 | `sha256_bhavc...` | `LICENSE_VERIFIED` |

## 2. Content-Based Versioning
Any modification to source data triggers a new version (`v1`, `v2`, etc.). Identical files are detected via SHA256 without creating redundant versions.
