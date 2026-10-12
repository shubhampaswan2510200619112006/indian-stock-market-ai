export type OrderSide = 'BUY' | 'SELL';
export type ProductType = 'INTRADAY' | 'DELIVERY';
export type OrderType = 'MARKET' | 'LIMIT';
export type OrderStatus = 'COMPLETED' | 'REJECTED' | 'CANCELLED' | 'OPEN';
export type OptionType = 'CE' | 'PE';

export interface PaperPosition {
  position_id: string;
  symbol: string;               // e.g. "NIFTY 24650 CE 17 OCT"
  underlying: string;           // "NIFTY", "BANKNIFTY", etc.
  strike: number;
  option_type: OptionType;
  expiry: string;
  product: ProductType;
  side: OrderSide;
  quantity: number;
  lots: number;
  lot_size: number;
  avg_price: number;
  current_ltp: number;
  prev_ltp?: number;
  invested_amount: number;
  current_value: number;
  pnl: number;
  pnl_percentage: number;
  day_pnl: number;
  tick_direction?: 'up' | 'down' | 'neutral';
  timestamp_ist: string;
  timestamp_ms: number;
}

export interface PaperOrder {
  order_id: string;
  symbol: string;
  underlying: string;
  strike: number;
  option_type: OptionType;
  expiry: string;
  side: OrderSide;
  product: ProductType;
  order_type: OrderType;
  quantity: number;
  lots: number;
  lot_size: number;
  price: number;
  execution_price: number;
  status: OrderStatus;
  timestamp_ist: string;
  timestamp_ms: number;
  execution_latency_ms: number;
  margin_used: number;
  rejection_reason?: string;
}

export interface PaperAccount {
  available_balance: number;
  initial_balance: number;
  invested_margin: number;
  portfolio_value: number;
  total_pnl: number;
  total_pnl_pct: number;
  day_pnl: number;
  day_pnl_pct: number;
  positions: PaperPosition[];
  orders: PaperOrder[];
}

export interface OptionLegQuote {
  ltp: number;
  change: number;
  change_pct: number;
  oi: number;
  oi_chg_pct: number;
  volume: number;
  iv: number;
  delta: number;
  bid: number;
  ask: number;
  tick_direction?: 'up' | 'down' | 'neutral';
}

export interface OptionStrikeRow {
  strike: number;
  is_atm: boolean;
  is_ce_itm: boolean;
  is_pe_itm: boolean;
  ce: OptionLegQuote;
  pe: OptionLegQuote;
}

export interface IndexInstrument {
  symbol: string;
  name: string;
  spot_price: number;
  change: number;
  change_pct: number;
  lot_size: number;
  strike_step: number;
  high: number;
  low: number;
  open: number;
  prev_close: number;
  pcr: number;
  max_pain: number;
  expiries: string[];
  active_expiry: string;
  tick_direction?: 'up' | 'down';
}
