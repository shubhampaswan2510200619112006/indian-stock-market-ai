export type DataStatus =
  | 'LIVE'
  | 'DELAYED'
  | 'HISTORICAL'
  | 'STALE'
  | 'UNAVAILABLE'
  | 'BLOCKED'
  | 'ERROR'
  | 'NO_DATA'
  | 'LOADING';

export interface MarketQuote {
  symbol: string;
  provider: string;
  last_price: number;
  bid_price: number | null;
  ask_price: number | null;
  volume: number;
  data_status: DataStatus;
  is_executable: boolean;
  execution_rejection_reason: string | null;
  price_classification: 'VALUATION_MARK_ONLY' | 'EXECUTION_QUOTE';
  timestamps: {
    provider_timestamp?: string;
    received_timestamp?: string;
    processed_timestamp?: string;
    latencies?: Record<string, number>;
  };
}

export interface Candle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  vwap?: number;
}

export interface OptionRow {
  strike_price: number;
  ce_oi: number;
  ce_volume: number;
  ce_iv: number;
  ce_ltp: number;
  ce_bid: number | null;
  ce_ask: number | null;
  ce_delta?: number;
  pe_oi: number;
  pe_volume: number;
  pe_iv: number;
  pe_ltp: number;
  pe_bid: number | null;
  pe_ask: number | null;
  pe_delta?: number;
}

export interface OptionChainSnapshot {
  underlying: string;
  spot_price: number;
  expiry: string;
  atm_strike: number;
  pcr: number;
  total_call_oi: number;
  total_put_oi: number;
  max_pain?: number;
  iv_regime?: 'LOW' | 'NORMAL' | 'ELEVATED' | 'EXTREME';
  rows: OptionRow[];
  status: DataStatus;
  reason?: string;
}

export interface ProviderHealth {
  name: string;
  type: string;
  status: 'CONNECTED' | 'DEGRADED' | 'STALE' | 'UNAVAILABLE' | 'CREDENTIAL_UNCONFIGURED';
  latency_ms: number | null;
  freshness_seconds: number | null;
  last_update?: string;
  error_rate_pct?: number;
  coverage_notes?: string;
}

export interface MarketRegime {
  symbol: string;
  regime: 'TREND' | 'RANGE' | 'BREAKOUT' | 'HIGH_VOLATILITY' | 'LOW_VOLATILITY' | 'TRANSITION';
  confidence: number;
  adx?: number;
  atr?: number;
  historical_volatility?: number;
  transition_probabilities?: Record<string, number>;
  data_status: DataStatus;
}

export interface ResearchHypothesis {
  hypothesis_id: string;
  title: string;
  target_event: string;
  horizon: string;
  oos_robustness_pts: number;
  statistical_evidence_pts: number;
  economic_significance_pts: number;
  total_score: number;
  is_shortlist_candidate: boolean;
  disqualification_reasons: string[];
}

export interface CalibratedProbability {
  target_event: string;
  horizon: string;
  probability: number;
  base_rate: number;
  brier_score: number;
  ece: number;
  calibration_status: 'CALIBRATED' | 'UNCALIBRATED' | 'INSUFFICIENT_SAMPLE';
  sample_size: number;
  ood_status: 'IN_DISTRIBUTION' | 'OOD_ALERT';
}

export interface GovernanceState {
  release_baseline: string;
  git_commit: string;
  tests_passing: number;
  tests_total: number;
  software_engineering: 'READY';
  investor_demo: 'READY';
  live_data: 'PARTIAL';
  options_research: 'PARTIAL';
  execution_research: 'BLOCKED';
  statistical_evidence: 'NO_DEMONSTRATED_EDGE / INSUFFICIENT';
  paired_bid_ask_coverage_pct: number;
  continuous_executable_surface_pct: number;
  allow_live_execution: boolean;
}
