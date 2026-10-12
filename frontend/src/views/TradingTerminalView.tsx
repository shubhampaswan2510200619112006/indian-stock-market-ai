import React, { useState } from 'react';
import { useRealtimeMarket } from '../hooks/useRealtimeMarket';
import { PrecisionMarketClock } from '../components/market/PrecisionMarketClock';
import { OptionChainTableDesk } from '../components/options/OptionChainTableDesk';
import { PortfolioDesk } from '../components/trading/PortfolioDesk';
import { CandlestickChart } from '../components/market/CandlestickChart';
import { LayoutGrid, Layers, BarChart2, TrendingUp, Activity, ShieldCheck, Zap } from 'lucide-react';

export type WorkspaceLayout = 'split' | 'options-only' | 'chart-only' | 'portfolio-only';

export const TradingTerminalView: React.FC = () => {
  const {
    instruments,
    selectedSymbol,
    setSelectedSymbol,
    selectedExpiry,
    setSelectedExpiry,
    activeInstrument,
    chainRows,
    timeState,
    intradayCandles,
  } = useRealtimeMarket();

  const [layoutMode, setLayoutMode] = useState<WorkspaceLayout>('split');
  const [chartTimeframe, setChartTimeframe] = useState<string>('5m');

  return (
    <div className="space-y-4">
      {/* 1. Precision Market Clock & High-Frequency Session Strip */}
      <PrecisionMarketClock timeState={timeState} />

      {/* 2. Executive Underlying Intelligence Strip */}
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
                  : 'bg-[#0a0e18]/80 border-white/[0.08] hover:border-white/[0.18] hover:bg-[#0e1424]'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-slate-300 font-['Outfit']">{inst.name}</span>
                <span
                  className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded ${
                    isUp ? 'bg-emerald-500/15 text-emerald-400' : 'bg-rose-500/15 text-rose-400'
                  }`}
                >
                  {isUp ? '+' : ''}{inst.change_pct.toFixed(2)}%
                </span>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-base font-extrabold font-mono text-white tracking-tight">
                  ₹{inst.spot_price.toLocaleString('en-IN', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  PCR: <strong className={inst.pcr >= 1 ? 'text-emerald-400' : 'text-slate-300'}>{inst.pcr.toFixed(2)}</strong>
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {/* 3. Professional Terminal Layout Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.08] pb-3 pt-1">
        <div className="flex items-center gap-1.5 bg-[#0a0e18]/90 p-1 rounded-xl border border-white/[0.08] text-xs">
          <button
            onClick={() => setLayoutMode('split')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer ${
              layoutMode === 'split'
                ? 'bg-[#d4af37]/20 text-[#f6d776] border border-[#d4af37]/40 shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
            title="Professional Dual Workspace: Simultaneous Live Options Chain + Real-time Technical Pattern Chart"
          >
            <LayoutGrid className="w-3.5 h-3.5" />
            <span>Dual Split Workspace</span>
          </button>

          <button
            onClick={() => setLayoutMode('options-only')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer ${
              layoutMode === 'options-only'
                ? 'bg-[#d4af37]/20 text-[#f6d776] border border-[#d4af37]/40 shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Options Expanded</span>
          </button>

          <button
            onClick={() => setLayoutMode('chart-only')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer ${
              layoutMode === 'chart-only'
                ? 'bg-[#d4af37]/20 text-[#f6d776] border border-[#d4af37]/40 shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <BarChart2 className="w-3.5 h-3.5" />
            <span>Chart & Pattern TA</span>
          </button>

          <button
            onClick={() => setLayoutMode('portfolio-only')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer ${
              layoutMode === 'portfolio-only'
                ? 'bg-[#d4af37]/20 text-[#f6d776] border border-[#d4af37]/40 shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <TrendingUp className="w-3.5 h-3.5" />
            <span>Positions & Ledger</span>
          </button>
        </div>

        {/* Right Active Underlying Badge */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-lg bg-white/[0.04] border border-white/[0.08] text-xs text-slate-300 font-mono">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>Active Contract: <strong className="text-white font-bold">{activeInstrument.name} (₹{activeInstrument.spot_price.toFixed(2)})</strong></span>
        </div>
      </div>

      {/* 4. Terminal Main Viewports */}

      {/* A. DUAL SPLIT WORKSPACE (THE REAL PROFESSIONAL TERMINAL LAYOUT) */}
      {layoutMode === 'split' && (
        <div className="space-y-5">
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 items-start">
            {/* Left 7 Columns (58%): Real-time Derivatives Chain */}
            <div className="xl:col-span-7 space-y-5">
              <OptionChainTableDesk
                instrument={activeInstrument}
                instruments={instruments}
                selectedSymbol={selectedSymbol}
                onSelectSymbol={setSelectedSymbol}
                selectedExpiry={selectedExpiry}
                onSelectExpiry={setSelectedExpiry}
                rows={chainRows}
                compact={true}
              />

              {/* Integrated Positions Dock below Chain for instant trade monitoring */}
              <PortfolioDesk
                onNavigateToOptions={() => setLayoutMode('options-only')}
                compact={true}
              />
            </div>

            {/* Right 5 Columns (42%): Real-Time Technical Analysis & Pattern Scanner */}
            <div className="xl:col-span-5 space-y-5 sticky top-20">
              <CandlestickChart
                candles={intradayCandles}
                symbol={activeInstrument.name}
                timeframe={chartTimeframe}
                onTimeframeChange={setChartTimeframe}
                currentPrice={activeInstrument.spot_price}
                istTime={timeState.timeWithMillis}
              />
            </div>
          </div>
        </div>
      )}

      {/* B. EXPANDED OPTIONS VIEW */}
      {layoutMode === 'options-only' && (
        <div className="space-y-5">
          <OptionChainTableDesk
            instrument={activeInstrument}
            instruments={instruments}
            selectedSymbol={selectedSymbol}
            onSelectSymbol={setSelectedSymbol}
            selectedExpiry={selectedExpiry}
            onSelectExpiry={setSelectedExpiry}
            rows={chainRows}
          />
        </div>
      )}

      {/* C. EXPANDED TECHNICAL CHART & PATTERN VIEW */}
      {layoutMode === 'chart-only' && (
        <div className="space-y-5">
          <CandlestickChart
            candles={intradayCandles}
            symbol={activeInstrument.name}
            timeframe={chartTimeframe}
            onTimeframeChange={setChartTimeframe}
            currentPrice={activeInstrument.spot_price}
            istTime={timeState.timeWithMillis}
          />
        </div>
      )}

      {/* D. EXPANDED PORTFOLIO VIEW */}
      {layoutMode === 'portfolio-only' && (
        <div className="space-y-5">
          <PortfolioDesk
            onNavigateToOptions={() => setLayoutMode('options-only')}
          />
        </div>
      )}
    </div>
  );
};
