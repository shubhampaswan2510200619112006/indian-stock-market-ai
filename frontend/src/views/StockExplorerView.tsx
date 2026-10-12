import React, { useState } from 'react';
import {
  TrendingUp, TrendingDown, Search, BarChart2, Layers,
  Sparkles, ShieldCheck, Bookmark, BookmarkCheck, ArrowUpRight,
  Activity, Clock, Sliders, Info, Zap
} from 'lucide-react';
import { useRealtimeMarket } from '../hooks/useRealtimeMarket';
import { usePaperTrading } from '../context/PaperTradingContext';
import { CandlestickChart } from '../components/market/CandlestickChart';
import { NavTab } from '../components/layout/Navigation';

interface StockExplorerViewProps {
  onNavigateToOptions?: () => void;
  onNavigateToAI?: () => void;
  onNavigateToPaper?: () => void;
}

export const StockExplorerView: React.FC<StockExplorerViewProps> = ({
  onNavigateToOptions,
  onNavigateToAI,
  onNavigateToPaper,
}) => {
  const {
    instruments,
    selectedSymbol,
    setSelectedSymbol,
    activeInstrument,
    intradayCandles,
    timeState,
  } = useRealtimeMarket();
  const { openOrderModal } = usePaperTrading();

  const [timeframe, setTimeframe] = useState<'1m' | '5m' | '15m' | '1D'>('5m');
  const [inWatchlist, setInWatchlist] = useState(false);
  const [selectedIndicator, setSelectedIndicator] = useState<'NONE' | 'RSI' | 'MACD' | 'BOLLINGER'>('NONE');

  const isUp = activeInstrument.change >= 0;

  // Extended statistics for deep dive
  const is52wHigh = activeInstrument.spot_price >= activeInstrument.high * 0.98;
  const range52wLow = activeInstrument.low * 0.85;
  const range52wHigh = activeInstrument.high * 1.15;

  const handleQuickBuy = () => {
    openOrderModal({
      symbol: `${activeInstrument.name} (Paper Spot)`,
      underlying: activeInstrument.name,
      strike: activeInstrument.spot_price,
      option_type: 'CE',
      expiry: activeInstrument.expiries[0] || '17 OCT 2026',
      side: 'BUY',
      product: 'INTRADAY',
      order_type: 'MARKET',
      quantity: activeInstrument.lot_size,
      lots: 1,
      lot_size: activeInstrument.lot_size,
      price: activeInstrument.spot_price,
    });
  };

  return (
    <div className="space-y-6">
      {/* ── 1. Top Instrument Switcher Strip ── */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-2xl bg-[#090d19]/90 border border-white/[0.08] backdrop-blur-xl">
        <div className="flex items-center gap-2 overflow-x-auto scrollbar-none py-1">
          {Object.keys(instruments).map((sym) => {
            const inst = instruments[sym];
            const isSelected = selectedSymbol === sym;
            const instUp = inst.change >= 0;

            return (
              <button
                key={sym}
                onClick={() => setSelectedSymbol(sym)}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-bold font-['Outfit'] transition-all flex items-center gap-2 cursor-pointer whitespace-nowrap ${
                  isSelected
                    ? 'bg-[#d4af37]/25 text-[#f6d776] border border-[#d4af37]/50 shadow-sm'
                    : 'bg-[#0d1424] text-slate-400 hover:text-white border border-white/[0.06] hover:bg-[#121c33]'
                }`}
              >
                <span>{inst.name}</span>
                <span className={`text-[10px] font-mono ${instUp ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {instUp ? '+' : ''}{inst.change_pct.toFixed(2)}%
                </span>
              </button>
            );
          })}
        </div>

        {/* Watchlist Bookmark toggle */}
        <button
          onClick={() => setInWatchlist(p => !p)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold border transition-all cursor-pointer ${
            inWatchlist
              ? 'bg-[#d4af37]/15 border-[#d4af37]/40 text-[#f6d776]'
              : 'bg-white/[0.04] border-white/[0.08] text-slate-400 hover:text-white'
          }`}
        >
          {inWatchlist ? <BookmarkCheck className="w-4 h-4 text-[#d4af37]" /> : <Bookmark className="w-4 h-4" />}
          <span>{inWatchlist ? 'In Watchlist' : '+ Watchlist'}</span>
        </button>
      </div>

      {/* ── 2. Primary Instrument Header Card ── */}
      <div className="p-6 rounded-2xl bg-[#090d19]/95 border border-white/[0.08] backdrop-blur-xl shadow-2xl">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 pb-6 border-b border-white/[0.08]">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-black text-white font-['Outfit'] tracking-tight">
                {activeInstrument.name}
              </h1>
              <span className="px-2.5 py-0.5 rounded-md text-xs font-mono font-bold bg-white/[0.08] text-slate-300">
                NSE: {activeInstrument.symbol}
              </span>
              <span className={`px-2 py-0.5 rounded-md text-[10px] font-mono font-bold uppercase ${
                isUp ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
              }`}>
                {isUp ? 'Bullish Drift' : 'Bearish Pressure'}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Contract Lot Size: {activeInstrument.lot_size} Units • Strike Step: ₹{activeInstrument.strike_step}
            </p>
          </div>

          {/* Current Spot Price Display */}
          <div className="flex items-baseline gap-4">
            <div className="text-3xl sm:text-4xl font-black font-mono text-white tracking-tight">
              ₹{activeInstrument.spot_price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div className="text-left">
              <div className={`text-base font-extrabold font-mono flex items-center gap-1 ${
                isUp ? 'text-emerald-400' : 'text-rose-400'
              }`}>
                {isUp ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                <span>{isUp ? '+' : ''}{activeInstrument.change.toFixed(2)}</span>
                <span>({isUp ? '+' : ''}{activeInstrument.change_pct.toFixed(2)}%)</span>
              </div>
              <div className="text-[10px] text-slate-400 font-mono">
                Prev Close: ₹{activeInstrument.prev_close.toFixed(2)}
              </div>
            </div>
          </div>

          {/* Quick Action CTAs */}
          <div className="flex items-center gap-2.5 w-full lg:w-auto">
            {onNavigateToOptions && (
              <button
                onClick={onNavigateToOptions}
                className="flex-1 lg:flex-none flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl bg-[#d4af37]/20 hover:bg-[#d4af37]/30 text-xs font-bold text-[#f6d776] border border-[#d4af37]/40 transition-all cursor-pointer shadow-sm"
              >
                <Layers className="w-4 h-4" />
                <span>Options Chain</span>
              </button>
            )}

            {onNavigateToAI && (
              <button
                onClick={onNavigateToAI}
                className="flex-1 lg:flex-none flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl bg-emerald-500/15 hover:bg-emerald-500/25 text-xs font-bold text-emerald-400 border border-emerald-500/30 transition-all cursor-pointer"
              >
                <Sparkles className="w-4 h-4" />
                <span>AI Insights</span>
              </button>
            )}

            <button
              onClick={handleQuickBuy}
              className="flex-1 lg:flex-none flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-xs font-extrabold text-black transition-all cursor-pointer shadow-lg shadow-emerald-500/20"
            >
              <span>Paper Trade</span>
            </button>
          </div>
        </div>

        {/* ── Microstructure Statistics Row ── */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 pt-5">
          <div className="p-3 rounded-xl bg-[#0c1222] border border-white/[0.04]">
            <div className="text-[10px] uppercase font-mono text-slate-400">Day High</div>
            <div className="text-sm font-bold font-mono text-white mt-0.5">₹{activeInstrument.high.toFixed(2)}</div>
          </div>
          <div className="p-3 rounded-xl bg-[#0c1222] border border-white/[0.04]">
            <div className="text-[10px] uppercase font-mono text-slate-400">Day Low</div>
            <div className="text-sm font-bold font-mono text-white mt-0.5">₹{activeInstrument.low.toFixed(2)}</div>
          </div>
          <div className="p-3 rounded-xl bg-[#0c1222] border border-white/[0.04]">
            <div className="text-[10px] uppercase font-mono text-slate-400">Open Price</div>
            <div className="text-sm font-bold font-mono text-white mt-0.5">₹{activeInstrument.open.toFixed(2)}</div>
          </div>
          <div className="p-3 rounded-xl bg-[#0c1222] border border-white/[0.04]">
            <div className="text-[10px] uppercase font-mono text-slate-400">Put-Call Ratio (PCR)</div>
            <div className="text-sm font-bold font-mono text-emerald-400 mt-0.5">{activeInstrument.pcr.toFixed(2)}</div>
          </div>
          <div className="p-3 rounded-xl bg-[#0c1222] border border-white/[0.04]">
            <div className="text-[10px] uppercase font-mono text-slate-400">Options Max Pain</div>
            <div className="text-sm font-bold font-mono text-[#f6d776] mt-0.5">₹{activeInstrument.max_pain}</div>
          </div>
          <div className="p-3 rounded-xl bg-[#0c1222] border border-white/[0.04]">
            <div className="text-[10px] uppercase font-mono text-slate-400">Nearest Expiry</div>
            <div className="text-sm font-bold font-mono text-white mt-0.5">{activeInstrument.expiries[0] || 'NEAR_MONTH'}</div>
          </div>
        </div>
      </div>

      {/* ── 3. High-Definition Interactive Chart View ── */}
      <div className="p-5 rounded-2xl bg-[#090d19]/90 border border-white/[0.08] backdrop-blur-xl shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pb-3 border-b border-white/[0.08]">
          <div className="flex items-center gap-2">
            <BarChart2 className="w-4 h-4 text-[#d4af37]" />
            <h2 className="text-sm font-extrabold text-white font-['Outfit'] uppercase tracking-wider">
              Candlestick Price Action & Volume
            </h2>
          </div>

          <div className="flex items-center gap-2">
            {/* Timeframe Selector */}
            <div className="flex items-center bg-[#0d1424] p-1 rounded-xl border border-white/[0.08] text-xs font-mono">
              {(['1m', '5m', '15m', '1D'] as const).map((tf) => (
                <button
                  key={tf}
                  onClick={() => setTimeframe(tf)}
                  className={`px-2.5 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                    timeframe === tf
                      ? 'bg-[#d4af37]/25 text-[#f6d776] border border-[#d4af37]/40 shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {tf}
                </button>
              ))}
            </div>

            {/* Technical Indicator Overlay Pills */}
            <div className="hidden sm:flex items-center bg-[#0d1424] p-1 rounded-xl border border-white/[0.08] text-xs">
              {(['NONE', 'RSI', 'MACD', 'BOLLINGER'] as const).map((ind) => (
                <button
                  key={ind}
                  onClick={() => setSelectedIndicator(ind)}
                  className={`px-2.5 py-1 rounded-lg font-bold transition-all cursor-pointer text-[10px] font-mono ${
                    selectedIndicator === ind
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {ind}
                </button>
              ))}
            </div>
          </div>
        </div>

        <CandlestickChart
          candles={intradayCandles}
          symbol={selectedSymbol}
          timeframe={timeframe}
          onTimeframeChange={(tf) => setTimeframe(tf as any)}
        />
      </div>

      {/* ── 4. Technical Indicators & Microstructure Panel ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="p-4 rounded-xl bg-[#090d19]/90 border border-white/[0.08]">
          <div className="text-xs font-bold text-slate-300 font-['Outfit'] mb-2 flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            <span>Relative Strength Index (RSI 14)</span>
          </div>
          <div className="text-2xl font-black font-mono text-emerald-400 mb-1">54.8</div>
          <div className="text-xs text-slate-400">
            Neutral Momentum. No extreme overbought or oversold exhaustion.
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#090d19]/90 border border-white/[0.08]">
          <div className="text-xs font-bold text-slate-300 font-['Outfit'] mb-2 flex items-center gap-2">
            <Sliders className="w-4 h-4 text-[#d4af37]" />
            <span>MACD (12, 26, 9)</span>
          </div>
          <div className="text-2xl font-black font-mono text-white mb-1">+14.2</div>
          <div className="text-xs text-slate-400">
            Mild Bullish Crossover above signal line on 15-minute timeframe.
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#090d19]/90 border border-white/[0.08]">
          <div className="text-xs font-bold text-slate-300 font-['Outfit'] mb-2 flex items-center gap-2">
            <Zap className="w-4 h-4 text-sky-400" />
            <span>VWAP Intraday Anchor</span>
          </div>
          <div className="text-2xl font-black font-mono text-sky-400 mb-1">+0.32% Above</div>
          <div className="text-xs text-slate-400">
            Trading above institutional volume weighted average price.
          </div>
        </div>
      </div>
    </div>
  );
};
