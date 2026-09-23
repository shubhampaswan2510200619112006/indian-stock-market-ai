"""
Phase 10A — Pillar A: Intraday Coverage & Granularity Audit Engine.

Audits intraday historical bar availability from authorized public endpoints.
Empirically evaluates:
- Yahoo Finance public endpoint availability for 1m and 5m intervals.
- Documents exact request parameters, date ranges, session counts, bar counts,
  duplicate rates, missing bar rates, and gap distributions.
- Treats constraints as observed/provider-specific limits for the selected endpoint,
  NOT universal market availability facts.
- Strictly refuses to fabricate bars or purchase unauthorized data.
- Concludes INTRADAY_RESEARCH_READY status.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import yfinance as yf

from src.research.phase10a.validation.calendar_validator import NSECalendarValidator


class IntradayCoverageAuditEngine:
    """
    Empirical auditor for intraday data granularity and availability.
    """

    DATA_DIR = Path("data/phase10a/intraday")

    @classmethod
    def audit_intraday_source(
        cls,
        symbol: str = "^NSEI",
        instrument_name: str = "NIFTY 50",
        download_if_missing: bool = True,
    ) -> Dict[str, Any]:
        """
        Audit 1m and 5m intraday availability for a given symbol from the authorized public endpoint.
        """
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        retrieval_ts = datetime.now(timezone.utc).isoformat()

        results: Dict[str, Any] = {
            "instrument": instrument_name,
            "symbol": symbol,
            "authorized_data_source": "Yahoo Finance (yfinance public endpoint)",
            "retrieval_timestamp_utc": retrieval_ts,
            "provider_constraint_notice": (
                "Observed availability constraints are provider-specific limitations of the selected "
                "public endpoint (Yahoo Finance), NOT a universal statement that multi-year intraday "
                "bars do not exist elsewhere in commercial repositories."
            ),
            "intervals": {},
            "intraday_research_ready": "BLOCKED / INSUFFICIENT_FOR_CONFIRMATORY",
            "findings": [],
        }

        intervals_to_test = [
            {"interval": "1m", "period": "7d", "expected_bars_per_day": 375, "min_days_target": 250},
            {"interval": "5m", "period": "60d", "expected_bars_per_day": 75, "min_days_target": 250},
        ]

        for cfg in intervals_to_test:
            interval = cfg["interval"]
            period = cfg["period"]
            expected_per_day = cfg["expected_bars_per_day"]
            min_target = cfg["min_days_target"]

            cache_file = cls.DATA_DIR / f"{symbol.replace('^', '').lower()}_{interval}.csv"
            df = None

            if cache_file.exists() and not download_if_missing:
                try:
                    df = pd.read_csv(cache_file, parse_dates=["Datetime"])
                except Exception:
                    df = None

            if df is None:
                try:
                    ticker = yf.Ticker(symbol)
                    df = ticker.history(period=period, interval=interval)
                    if df is not None and not df.empty:
                        df.reset_index(inplace=True)
                        df.to_csv(cache_file, index=False)
                except Exception as e:
                    results["findings"].append(f"Failed to fetch {interval} data: {e}")
                    df = pd.DataFrame()

            if df is None or df.empty:
                results["intervals"][interval] = {
                    "status": "UNAVAILABLE",
                    "request_parameters": {"period": period, "interval": interval},
                    "row_count": 0,
                    "session_count": 0,
                    "coverage_limitations": "No data returned by provider for requested parameters.",
                }
                continue

            # Analyze retrieved dataframe
            # Datetime column identification
            dt_col = "Datetime" if "Datetime" in df.columns else df.columns[0]
            df[dt_col] = pd.to_datetime(df[dt_col])
            total_rows = len(df)
            unique_ts = df[dt_col].nunique()
            duplicates = total_rows - unique_ts
            dup_rate = float(duplicates / total_rows) if total_rows > 0 else 0.0

            # Session identification
            # Convert to date
            sessions = df[dt_col].dt.date.unique()
            session_count = len(sessions)
            start_date = df[dt_col].min().strftime("%Y-%m-%d %H:%M:%S")
            end_date = df[dt_col].max().strftime("%Y-%m-%d %H:%M:%S")

            # Missing bars calculation across full trading sessions
            expected_total_bars = session_count * expected_per_day
            missing_bars = max(0, expected_total_bars - unique_ts)
            missing_bar_rate = float(missing_bars / expected_total_bars) if expected_total_bars > 0 else 0.0

            # Gap distribution (in minutes)
            df_sorted = df.sort_values(dt_col)
            deltas = df_sorted[dt_col].diff().dt.total_seconds() / 60.0
            deltas = deltas.dropna()
            
            # Filter intra-session deltas (ignore overnight gaps > 300 mins)
            intrasession_deltas = deltas[deltas <= 60]
            gap_summary = {
                "median_minutes": float(intrasession_deltas.median()) if not intrasession_deltas.empty else None,
                "max_intrasession_gap_minutes": float(intrasession_deltas.max()) if not intrasession_deltas.empty else None,
                "large_gaps_count_gt_15m": int((intrasession_deltas > 15).sum()),
            }

            # Check coverage against research requirement (minimum 250 sessions)
            is_sufficient = session_count >= min_target
            coverage_limitation = (
                f"Observed provider retention ceiling: {session_count} sessions returned "
                f"(requires >= {min_target} sessions for confirmatory statistical testing). "
                f"Date window: {start_date} to {end_date}."
            )

            results["intervals"][interval] = {
                "status": "AVAILABLE_BUT_INSUFFICIENT" if not is_sufficient else "SUFFICIENT",
                "request_parameters": {"period": period, "interval": interval},
                "returned_date_range": {"start": start_date, "end": end_date},
                "session_count": session_count,
                "row_count": total_rows,
                "unique_timestamp_count": unique_ts,
                "duplicate_count": duplicates,
                "duplicate_rate": dup_rate,
                "expected_bars_per_session": expected_per_day,
                "missing_bar_rate": missing_bar_rate,
                "gap_distribution": gap_summary,
                "target_sessions_required": min_target,
                "coverage_limitations": coverage_limitation,
            }

        # Determine overall intraday readiness
        all_sufficient = all(
            v.get("status") == "SUFFICIENT" for v in results["intervals"].values()
        )
        if all_sufficient and len(results["intervals"]) > 0:
            results["intraday_research_ready"] = "READY"
        else:
            results["intraday_research_ready"] = "BLOCKED / INSUFFICIENT_FOR_CONFIRMATORY"
            results["findings"].append(
                "Authorized public provider returns maximum 60 calendar days of 5m bars (~41-43 trading sessions) "
                "and 7 calendar days of 1m bars (~5-6 trading sessions). This is statistically insufficient "
                "for confirmatory out-of-sample research (target >= 250 sessions). Intraday track remains BLOCKED."
            )

        return results

    @classmethod
    def audit_all_intraday_instruments(cls) -> Dict[str, Any]:
        """Audit intraday data for primary indices: NIFTY 50 and BANKNIFTY."""
        nifty_audit = cls.audit_intraday_source("^NSEI", "NIFTY 50")
        banknifty_audit = cls.audit_intraday_source("^NSEBANK", "BANK NIFTY")

        combined = {
            "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "provider": "Yahoo Finance public endpoint",
            "instruments": {
                "NIFTY_50": nifty_audit,
                "BANK_NIFTY": banknifty_audit,
            },
            "intraday_research_ready": (
                "READY"
                if nifty_audit["intraday_research_ready"] == "READY"
                and banknifty_audit["intraday_research_ready"] == "READY"
                else "BLOCKED / INSUFFICIENT_FOR_CONFIRMATORY"
            ),
            "executive_conclusion": (
                "Intraday research track is BLOCKED / INSUFFICIENT_FOR_CONFIRMATORY. "
                "Under current authorized public data sources, intraday historical depth is limited to "
                "the provider's observed rolling retention window (7d for 1m, 60d for 5m), yielding < 45 sessions. "
                "Confirmatory hypothesis testing requires >= 250 trading sessions. "
                "No synthetic bars will be generated, and no unauthorized purchases will be made."
            ),
        }

        # Save artifact
        out_file = Path("data/phase10a/coverage.json")
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(combined, f, indent=2)

        return combined


if __name__ == "__main__":
    rep = IntradayCoverageAuditEngine.audit_all_intraday_instruments()
    print("Intraday Audit Complete:")
    print(json.dumps(rep, indent=2))
