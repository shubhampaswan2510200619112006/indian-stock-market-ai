import React, { useState } from 'react';
import { useRealtimeMarket } from '../hooks/useRealtimeMarket';
import { PrecisionMarketClock } from '../components/market/PrecisionMarketClock';
import { OptionChainTableDesk } from '../components/options/OptionChainTableDesk';
import { PortfolioDesk } from '../components/trading/PortfolioDesk';
import { CandlestickChart } from '../components/market/CandlestickChart';
import { MLEngineSignalCard } from '../components/trading/MLEngineSignalCard';

interface TradingTerminalViewProps {
  onNavigateToOptions?: () => void;
}

export const TradingTerminalView: React.FC<TradingTerminalViewProps> = ({
  onNavigateToOptions,
}) => {
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

  const [chartTimeframe, setChartTimeframe] = useState<string>('5m');

  return (
    <div className="space-y-4">
      {/* 1. Precision Market Clock & High-Frequency Session Strip */}
      <PrecisionMarketClock timeState={timeState} />

      {/* 2. AI ML Predictive Alpha Signals Engine (What to Buy & What to Sell) */}
      <MLEngineSignalCard
        currentSpot={activeInstrument.spot_price}
        onNavigateToOptions={onNavigateToOptions}
      />

      {/* 3. Executive Underlying Intelligence Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
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

      {/* 3. Real-Time Workspace */}
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

            {/* Quick Positions Dock */}
            <PortfolioDesk
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
    </div>
  );
};
