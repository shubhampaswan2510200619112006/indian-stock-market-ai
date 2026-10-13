import React, { useState } from 'react';
import { useRealtimeMarket } from '../hooks/useRealtimeMarket';
import { CandlestickChart } from '../components/market/CandlestickChart';
import {
  TrendingUp, TrendingDown, Activity, Sparkles, Compass,
  Layers, Gauge, BarChart2, ShieldCheck, Zap, ArrowUpRight, ArrowDownRight
} from 'lucide-react';

export const TechnicalAnalysisDeskView: React.FC = () => {
  const {
    instruments,
    selectedSymbol,
    setSelectedSymbol,
    activeInstrument,
    timeState,
    intradayCandles,
    chartTimeframe,
    setChartTimeframe,
  } = useRealtimeMarket();

  const spot = activeInstrument.spot_price;
  const pivot = Math.round(spot / 50) * 50;
  const r1 = pivot + 45;
  const r2 = pivot + 90;
  const s1 = pivot - 40;
  const s2 = pivot - 85;

  return (
    <div className="space-y-5">
      {/* 1. Underlying Selector Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {Object.keys(instruments).map((sym) => {
          const inst = instruments[sym];
          const isSelected = selectedSymbol === sym;
          const isUp = inst.change >= 0;

          return (
            <button
              key={sym}
              onClick={() => setSelectedSymbol(sym)}
              className={`text-left p-3 rounded-xl border transition-all cursor-pointer backdrop-blur-md ${
                isSelected
                  ? 'bg-[#101728] border-[#d4af37]/60 shadow-[0_4px_20px_rgba(212,175,55,0.12)]'
                  : 'bg-[#0a0e18]/80 border-white/[0.08] hover:border-white/[0.18]'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-slate-300 font-['Outfit']">{inst.name}</span>
                <span className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded ${
                  isUp ? 'bg-emerald-500/15 text-emerald-400' : 'bg-rose-500/15 text-rose-400'
                }`}>
                  {isUp ? '+' : ''}{inst.change_pct.toFixed(2)}%
                </span>
              </div>
              <div className="text-base font-extrabold font-mono text-white">
                ₹{inst.spot_price.toLocaleString('en-IN', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
              </div>
            </button>
          );
        })}
      </div>

      {/* 2. Main Workstation: Chart + Technical Oscillators Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 items-start">
        {/* Left 8 Cols: Comprehensive Interactive Candlestick Chart */}
        <div className="xl:col-span-8 space-y-5">
          <CandlestickChart
            candles={intradayCandles}
            symbol={activeInstrument.name}
            timeframe={chartTimeframe}
            onTimeframeChange={setChartTimeframe}
            currentPrice={activeInstrument.spot_price}
            istTime={timeState.timeWithMillis}
          />

          {/* AI Pattern Detection Radar */}
          <div className="rounded-2xl bg-[#090e1a]/90 border border-white/[0.08] p-4">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-4 h-4 text-[#d4af37]" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-white font-mono">
                Automated Candlestick Pattern Radar
              </h3>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/25">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-emerald-300">Bullish Engulfing</span>
                  <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-1.5 py-0.2 rounded font-bold">5m</span>
                </div>
                <div className="text-[11px] text-slate-300">Buyer momentum expanded beyond previous candle range.</div>
              </div>

              <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/25">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-emerald-300">Hammer Reversal</span>
                  <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-1.5 py-0.2 rounded font-bold">15m</span>
                </div>
                <div className="text-[11px] text-slate-300">Long lower shadow rejects key demand floor at ₹24,630.</div>
              </div>

              <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/25">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-amber-300">Doji Indecision</span>
                  <span className="text-[10px] bg-amber-500/20 text-amber-300 px-1.5 py-0.2 rounded font-bold">1m</span>
                </div>
                <div className="text-[11px] text-slate-300">Equilibrium pause near ₹24,650 ATM strike cluster.</div>
              </div>

              <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/25">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-purple-300">S/R Breakout</span>
                  <span className="text-[10px] bg-purple-500/20 text-purple-300 px-1.5 py-0.2 rounded font-bold">1h</span>
                </div>
                <div className="text-[11px] text-slate-300">Breakout confirmed above morning session resistance line.</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right 4 Cols: Key Technical Indicators, Pivot Levels & Oscillators */}
        <div className="xl:col-span-4 space-y-5">
          {/* AI Price Action Verdict */}
          <div className="rounded-2xl bg-gradient-to-br from-[#0c1322] to-[#11192e] border border-[#d4af37]/35 p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono font-bold text-[#f6d776] uppercase tracking-wide">
                Price Action Verdict
              </span>
              <span className="text-xs font-extrabold text-emerald-400 bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.5 rounded-full">
                BULLISH STRUCTURE
              </span>
            </div>
            <div className="text-sm font-bold text-white mb-1">
              Higher Highs & Higher Lows Cycle
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Price is trending above intraday VWAP with positive volume expansion. Favorable risk-reward for long calls on retests of ₹{s1}.
            </p>
          </div>

          {/* Key Oscillators & Metrics */}
          <div className="rounded-2xl bg-[#090e1a]/90 border border-white/[0.08] p-4 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono mb-2">
              Technical Oscillators
            </h3>

            <div className="flex items-center justify-between py-2 border-b border-white/[0.06] text-xs">
              <span className="text-slate-400">RSI (14 Period)</span>
              <span className="font-mono font-bold text-emerald-400">62.40 (Bullish Momentum)</span>
            </div>

            <div className="flex items-center justify-between py-2 border-b border-white/[0.06] text-xs">
              <span className="text-slate-400">MACD (12, 26, 9)</span>
              <span className="font-mono font-bold text-emerald-400">+14.20 (Positive Crossover)</span>
            </div>

            <div className="flex items-center justify-between py-2 border-b border-white/[0.06] text-xs">
              <span className="text-slate-400">Intraday VWAP</span>
              <span className="font-mono font-bold text-white">₹{(spot - 34.4).toFixed(2)} (Above)</span>
            </div>

            <div className="flex items-center justify-between py-2 border-b border-white/[0.06] text-xs">
              <span className="text-slate-400">ADX Trend Strength</span>
              <span className="font-mono font-bold text-cyan-300">28.40 (Strong Trend)</span>
            </div>

            <div className="flex items-center justify-between py-2 text-xs">
              <span className="text-slate-400">India VIX</span>
              <span className="font-mono font-bold text-[#f6d776]">15.25 (Stable Range)</span>
            </div>
          </div>

          {/* Pivot Points & S/R Zones */}
          <div className="rounded-2xl bg-[#090e1a]/90 border border-white/[0.08] p-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono mb-3">
              Standard Pivot Levels & Targets
            </h3>

            <div className="space-y-2 font-mono text-xs">
              <div className="flex items-center justify-between p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300">
                <span>Resistance 2 (R2)</span>
                <span className="font-bold">₹{r2.toLocaleString('en-IN')}</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-rose-500/5 border border-rose-500/15 text-rose-400">
                <span>Resistance 1 (R1)</span>
                <span className="font-bold">₹{r1.toLocaleString('en-IN')}</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-white/[0.04] border border-white/[0.1] text-white">
                <span className="font-bold">Central Pivot Point</span>
                <span className="font-extrabold text-[#f6d776]">₹{pivot.toLocaleString('en-IN')}</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-emerald-500/5 border border-emerald-500/15 text-emerald-400">
                <span>Support 1 (S1)</span>
                <span className="font-bold">₹{s1.toLocaleString('en-IN')}</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300">
                <span>Support 2 (S2)</span>
                <span className="font-bold">₹{s2.toLocaleString('en-IN')}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
