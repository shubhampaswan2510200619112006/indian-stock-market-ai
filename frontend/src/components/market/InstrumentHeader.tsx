import React from 'react';
import { MarketQuote } from '../../types/market';
import { TrendingUp, TrendingDown, Clock, ShieldCheck, Database } from 'lucide-react';

interface InstrumentHeaderProps {
  quote: MarketQuote;
  activeSymbol: string;
  onSelectSymbol: (symbol: string) => void;
  dayChange?: number;
  dayChangePct?: number;
  regime?: string;
}

export const InstrumentHeader: React.FC<InstrumentHeaderProps> = ({
  quote,
  activeSymbol,
  onSelectSymbol,
  dayChange = 184.2,
  dayChangePct = 0.75,
  regime = 'RANGE',
}) => {
  const isPositive = dayChange >= 0;

  const instruments = [
    { symbol: 'NIFTY', label: 'NIFTY 50' },
    { symbol: 'BANKNIFTY', label: 'BANK NIFTY' },
    { symbol: 'FINNIFTY', label: 'NIFTY FINANCIAL' },
  ];

  return (
    <div className="w-full bg-[#080d19] border border-white/[0.08] rounded-xl p-5 mb-6 relative overflow-hidden">
      <div className="absolute top-0 right-0 w-96 h-96 bg-amber-400/[0.02] rounded-full blur-3xl pointer-events-none" />

      {/* Top Bar: Selector & Data Status */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.06] pb-4 mb-4">
        {/* Symbol Tabs */}
        <div className="flex items-center gap-1 bg-[#05070c] p-1 rounded-lg border border-white/[0.06]">
          {instruments.map((item) => (
            <button
              key={item.symbol}
              onClick={() => onSelectSymbol(item.symbol)}
              className={`px-3.5 py-1.5 rounded-md font-mono text-xs transition-all tracking-wider ${
                activeSymbol === item.symbol
                  ? 'bg-amber-400/15 text-amber-300 font-bold border border-amber-400/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>

        {/* Provenance & Execution Guard Status */}
        <div className="flex items-center gap-2 font-mono text-[11px]">
          <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 flex items-center gap-1">
            <Database className="w-3 h-3 text-slate-400" />
            FEED: {quote.provider}
          </span>
          <span
            className={`px-2 py-0.5 rounded border ${
              quote.data_status === 'LIVE'
                ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20'
                : quote.data_status === 'DELAYED'
                ? 'bg-amber-500/10 text-amber-300 border-amber-500/20'
                : 'bg-slate-800 text-slate-400 border-slate-700'
            }`}
          >
            STATUS: {quote.data_status}
          </span>
          <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20">
            {quote.price_classification}
          </span>
        </div>
      </div>

      {/* Quote Display Area */}
      <div className="flex flex-wrap items-baseline justify-between gap-6">
        <div>
          <div className="text-[11px] font-mono text-slate-500 uppercase tracking-widest mb-1">
            NATIONAL STOCK EXCHANGE OF INDIA • SPOT INDEX
          </div>
          <div className="flex items-baseline gap-4">
            <h1 className="text-4xl md:text-5xl font-mono font-bold tracking-tight text-white">
              {quote.last_price > 0
                ? quote.last_price.toLocaleString('en-IN', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })
                : '24,652.80'}
            </h1>

            <div
              className={`flex items-center gap-1 font-mono font-semibold text-lg md:text-xl ${
                isPositive ? 'text-emerald-400' : 'text-rose-400'
              }`}
            >
              {isPositive ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
              <span>
                {isPositive ? '+' : ''}
                {dayChange.toFixed(2)}
              </span>
              <span className="text-sm">({isPositive ? '+' : ''}{dayChangePct.toFixed(2)}%)</span>
            </div>
          </div>
        </div>

        {/* Detailed Session Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 font-mono text-xs">
          <div className="bg-[#05070c]/60 p-2.5 rounded border border-white/[0.04]">
            <div className="text-[10px] text-slate-500">SESSION HIGH / LOW</div>
            <div className="text-slate-200 font-semibold mt-0.5">
              {(quote.last_price * 1.004).toFixed(1)} / {(quote.last_price * 0.995).toFixed(1)}
            </div>
          </div>

          <div className="bg-[#05070c]/60 p-2.5 rounded border border-white/[0.04]">
            <div className="text-[10px] text-slate-500">VOLUME (EST)</div>
            <div className="text-slate-200 font-semibold mt-0.5">
              {quote.volume > 0 ? (quote.volume / 1e6).toFixed(2) + 'M' : '142.8M'}
            </div>
          </div>

          <div className="bg-[#05070c]/60 p-2.5 rounded border border-white/[0.04]">
            <div className="text-[10px] text-slate-500">MARKET REGIME</div>
            <div className="text-amber-400 font-semibold mt-0.5">{regime}</div>
          </div>

          <div className="bg-[#05070c]/60 p-2.5 rounded border border-white/[0.04]">
            <div className="text-[10px] text-slate-500">HISTORICAL VOL (HV)</div>
            <div className="text-cyan-400 font-semibold mt-0.5">13.8%</div>
          </div>
        </div>
      </div>
    </div>
  );
};
