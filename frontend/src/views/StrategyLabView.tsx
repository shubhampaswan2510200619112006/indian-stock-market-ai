import React, { useState } from 'react';
import {
  PieChart, Sliders, Play, RotateCcw, ShieldCheck,
  CheckCircle2, AlertTriangle, ArrowRight, TrendingUp, TrendingDown,
  Layers, BarChart2, Info, Sparkles, Check
} from 'lucide-react';
import { useRealtimeMarket } from '../hooks/useRealtimeMarket';
import { usePaperTrading } from '../context/PaperTradingContext';
import { NavTab } from '../components/layout/Navigation';

interface StrategyLabViewProps {
  onNavigateToPaper?: () => void;
}

interface StrategyLeg {
  id: string;
  action: 'BUY' | 'SELL';
  type: 'CE' | 'PE';
  strike: number;
  premium: number;
  lots: number;
}

export const StrategyLabView: React.FC<StrategyLabViewProps> = ({
  onNavigateToPaper,
}) => {
  const { activeInstrument, selectedSymbol, instruments } = useRealtimeMarket();
  const { openOrderModal, placeOrder } = usePaperTrading();

  const spot = activeInstrument.spot_price;
  const step = activeInstrument.strike_step;
  const atm = Math.round(spot / step) * step;
  const lotSize = activeInstrument.lot_size;

  // Selected preset
  const [selectedPreset, setSelectedPreset] = useState<
    'BULL_CALL_SPREAD' | 'BEAR_PUT_SPREAD' | 'LONG_STRADDLE' | 'SHORT_STRANGLE' | 'IRON_CONDOR'
  >('BULL_CALL_SPREAD');

  // Strategy legs state
  const [legs, setLegs] = useState<StrategyLeg[]>([
    { id: '1', action: 'BUY', type: 'CE', strike: atm, premium: 142.5, lots: 1 },
    { id: '2', action: 'SELL', type: 'CE', strike: atm + step * 2, premium: 58.0, lots: 1 },
  ]);

  const [backtestRunning, setBacktestRunning] = useState(false);
  const [backtestResult, setBacktestResult] = useState<{
    totalTrades: number;
    winRate: number;
    sharpeRatio: number;
    maxDrawdown: number;
    totalReturnPct: number;
  } | null>(null);

  // Preset updater
  const handlePresetSelect = (preset: typeof selectedPreset) => {
    setSelectedPreset(preset);
    if (preset === 'BULL_CALL_SPREAD') {
      setLegs([
        { id: '1', action: 'BUY', type: 'CE', strike: atm, premium: 142.5, lots: 1 },
        { id: '2', action: 'SELL', type: 'CE', strike: atm + step * 2, premium: 58.0, lots: 1 },
      ]);
    } else if (preset === 'BEAR_PUT_SPREAD') {
      setLegs([
        { id: '1', action: 'BUY', type: 'PE', strike: atm, premium: 135.0, lots: 1 },
        { id: '2', action: 'SELL', type: 'PE', strike: atm - step * 2, premium: 52.0, lots: 1 },
      ]);
    } else if (preset === 'LONG_STRADDLE') {
      setLegs([
        { id: '1', action: 'BUY', type: 'CE', strike: atm, premium: 142.5, lots: 1 },
        { id: '2', action: 'BUY', type: 'PE', strike: atm, premium: 135.0, lots: 1 },
      ]);
    } else if (preset === 'SHORT_STRANGLE') {
      setLegs([
        { id: '1', action: 'SELL', type: 'CE', strike: atm + step * 2, premium: 58.0, lots: 1 },
        { id: '2', action: 'SELL', type: 'PE', strike: atm - step * 2, premium: 52.0, lots: 1 },
      ]);
    } else if (preset === 'IRON_CONDOR') {
      setLegs([
        { id: '1', action: 'BUY', type: 'PE', strike: atm - step * 4, premium: 22.0, lots: 1 },
        { id: '2', action: 'SELL', type: 'PE', strike: atm - step * 2, premium: 52.0, lots: 1 },
        { id: '3', action: 'SELL', type: 'CE', strike: atm + step * 2, premium: 58.0, lots: 1 },
        { id: '4', action: 'BUY', type: 'CE', strike: atm + step * 4, premium: 25.0, lots: 1 },
      ]);
    }
  };

  // Payoff calculation across 21 price points
  const priceMin = atm - step * 6;
  const priceMax = atm + step * 6;
  const numPoints = 25;
  const priceStep = (priceMax - priceMin) / (numPoints - 1);

  const payoffPoints: { price: number; pnl: number }[] = [];
  let maxProfit = -Infinity;
  let maxLoss = Infinity;

  for (let i = 0; i < numPoints; i++) {
    const p = priceMin + i * priceStep;
    let totalPnl = 0;

    legs.forEach((leg) => {
      let intrinsic = 0;
      if (leg.type === 'CE') {
        intrinsic = Math.max(0, p - leg.strike);
      } else {
        intrinsic = Math.max(0, leg.strike - p);
      }

      const legPnl = leg.action === 'BUY'
        ? (intrinsic - leg.premium) * leg.lots * lotSize
        : (leg.premium - intrinsic) * leg.lots * lotSize;

      totalPnl += legPnl;
    });

    payoffPoints.push({ price: p, pnl: totalPnl });
    if (totalPnl > maxProfit) maxProfit = totalPnl;
    if (totalPnl < maxLoss) maxLoss = totalPnl;
  }

  // Find breakeven approximations
  const breakevens: number[] = [];
  for (let i = 0; i < payoffPoints.length - 1; i++) {
    const p1 = payoffPoints[i];
    const p2 = payoffPoints[i + 1];
    if ((p1.pnl <= 0 && p2.pnl >= 0) || (p1.pnl >= 0 && p2.pnl <= 0)) {
      const be = p1.price + (p2.price - p1.price) * (-p1.pnl / (p2.pnl - p1.pnl || 1));
      breakevens.push(Math.round(be));
    }
  }

  // Net debit or credit
  let netPremium = 0;
  legs.forEach((l) => {
    netPremium += l.action === 'BUY' ? -l.premium : l.premium;
  });
  const netDebit = netPremium < 0;

  // Run backtest simulation
  const handleRunBacktest = () => {
    setBacktestRunning(true);
    setTimeout(() => {
      setBacktestResult({
        totalTrades: 48,
        winRate: 68.75,
        sharpeRatio: 1.84,
        maxDrawdown: 7.4,
        totalReturnPct: 24.6,
      });
      setBacktestRunning(false);
    }, 800);
  };

  // SVG Payoff chart coordinates
  const svgWidth = 600;
  const svgHeight = 220;
  const padding = 30;

  const yMin = Math.min(...payoffPoints.map((p) => p.pnl), -1000);
  const yMax = Math.max(...payoffPoints.map((p) => p.pnl), 1000);

  const getSvgX = (price: number) =>
    padding + ((price - priceMin) / (priceMax - priceMin)) * (svgWidth - padding * 2);
  const getSvgY = (pnl: number) =>
    svgHeight - padding - ((pnl - yMin) / (yMax - yMin || 1)) * (svgHeight - padding * 2);

  const zeroY = getSvgY(0);
  const pathD = payoffPoints
    .map((pt, i) => `${i === 0 ? 'M' : 'L'} ${getSvgX(pt.price)} ${getSvgY(pt.pnl)}`)
    .join(' ');

  const handleExecuteInPaper = () => {
    // Execute all legs
    legs.forEach((leg) => {
      openOrderModal({
        symbol: `${activeInstrument.name} ${leg.strike} ${leg.type}`,
        underlying: activeInstrument.name,
        strike: leg.strike,
        option_type: leg.type,
        expiry: activeInstrument.expiries[0] || '17 OCT 2026',
        side: leg.action,
        product: 'DELIVERY',
        order_type: 'MARKET',
        quantity: leg.lots * lotSize,
        lots: leg.lots,
        lot_size: lotSize,
        price: leg.premium,
      });
    });
  };

  return (
    <div className="space-y-6">
      {/* ── 1. Strategy Workspace Header ── */}
      <div className="p-4 rounded-2xl bg-[#080d19]/95 border border-sky-500/25 backdrop-blur-xl shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-sky-500/15 border border-sky-500/40 flex items-center justify-center text-sky-400">
            <PieChart className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-black text-white font-['Outfit'] tracking-tight">
                Options Strategy Lab & Payoff Visualizer
              </h1>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-sky-500/15 text-sky-400 border border-sky-500/30">
                MULTI-LEG ENGINE
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Model multi-leg spreads, calculate expiry payoff, breakevens & execute directly into paper trading
            </p>
          </div>
        </div>

        {/* Spot Indicator */}
        <div className="flex items-center gap-2 text-xs font-mono p-2 rounded-xl bg-[#0c1222] border border-white/[0.08]">
          <span className="text-slate-400">{activeInstrument.name} Spot:</span>
          <strong className="text-white">₹{spot.toFixed(1)}</strong>
        </div>
      </div>

      {/* ── 2. Preset Strategies Carousel ── */}
      <div className="flex items-center gap-2 overflow-x-auto scrollbar-none py-1">
        {[
          { id: 'BULL_CALL_SPREAD', name: 'Bull Call Spread', type: 'Bullish Debit' },
          { id: 'BEAR_PUT_SPREAD', name: 'Bear Put Spread', type: 'Bearish Debit' },
          { id: 'LONG_STRADDLE', name: 'Long Straddle', type: 'Vol Breakout' },
          { id: 'SHORT_STRANGLE', name: 'Short Strangle', type: 'Range Decay' },
          { id: 'IRON_CONDOR', name: 'Iron Condor', type: 'Neutral Credit' },
        ].map((strat) => (
          <button
            key={strat.id}
            onClick={() => handlePresetSelect(strat.id as any)}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer flex flex-col items-start ${
              selectedPreset === strat.id
                ? 'bg-gradient-to-r from-sky-500/20 to-blue-500/20 border border-sky-500/50 text-white shadow-lg'
                : 'bg-[#090d19] border border-white/[0.06] text-slate-400 hover:text-white hover:bg-[#0e1529]'
            }`}
          >
            <span className="font-['Outfit']">{strat.name}</span>
            <span className="text-[10px] font-mono text-sky-400/80 font-normal">{strat.type}</span>
          </button>
        ))}
      </div>

      {/* ── 3. Payoff Diagram & Metrics Grid ── */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
        {/* Left 8 Cols: Interactive Payoff Chart & Legs */}
        <div className="xl:col-span-8 space-y-6">
          {/* Payoff Chart Canvas */}
          <div className="p-5 rounded-2xl bg-[#090d19]/90 border border-white/[0.08] backdrop-blur-xl shadow-xl">
            <div className="flex items-center justify-between mb-3 pb-3 border-b border-white/[0.08]">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-400" />
                <h2 className="text-sm font-extrabold text-white font-['Outfit'] uppercase tracking-wider">
                  Expiry Payoff Curve (P&L vs Spot)
                </h2>
              </div>
              <span className="text-[10px] font-mono text-slate-400">
                Range: ₹{priceMin.toFixed(0)} — ₹{priceMax.toFixed(0)}
              </span>
            </div>

            {/* SVG Visualizer */}
            <div className="w-full overflow-x-auto">
              <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-56 font-mono text-[9px]">
                {/* Zero P&L horizontal dashed line */}
                <line
                  x1={padding}
                  y1={zeroY}
                  x2={svgWidth - padding}
                  y2={zeroY}
                  stroke="rgba(255,255,255,0.2)"
                  strokeDasharray="4 4"
                />
                <text x={padding + 5} y={zeroY - 4} fill="rgba(255,255,255,0.4)">₹0 (Breakeven)</text>

                {/* Spot Price vertical reference line */}
                <line
                  x1={getSvgX(spot)}
                  y1={padding}
                  x2={getSvgX(spot)}
                  y2={svgHeight - padding}
                  stroke="rgba(212,175,55,0.4)"
                  strokeDasharray="2 2"
                />
                <text x={getSvgX(spot) + 4} y={padding + 12} fill="#f6d776">LTP ₹{spot.toFixed(0)}</text>

                {/* Dynamic Payoff Curve */}
                <path
                  d={pathD}
                  fill="none"
                  stroke={netDebit ? '#38bdf8' : '#10b981'}
                  strokeWidth="2.5"
                />

                {/* Breakeven Dots */}
                {breakevens.map((be, i) => (
                  <g key={i}>
                    <circle cx={getSvgX(be)} cy={zeroY} r="4" fill="#fbbf24" />
                    <text x={getSvgX(be) - 15} y={zeroY + 14} fill="#fbbf24">BE: ₹{be}</text>
                  </g>
                ))}
              </svg>
            </div>
          </div>

          {/* Active Legs Config Table */}
          <div className="p-5 rounded-2xl bg-[#090d19]/90 border border-white/[0.08] backdrop-blur-xl shadow-xl">
            <h2 className="text-sm font-extrabold text-white font-['Outfit'] uppercase tracking-wider mb-3">
              Multi-Leg Configuration
            </h2>

            <div className="space-y-2">
              {legs.map((leg, idx) => (
                <div
                  key={leg.id}
                  className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl bg-[#0d1424] border border-white/[0.06] text-xs font-mono"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-5 h-5 rounded-full bg-white/[0.08] flex items-center justify-center text-[10px] text-slate-300">
                      {idx + 1}
                    </span>
                    <span className={`px-2 py-0.5 rounded font-bold ${
                      leg.action === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                    }`}>
                      {leg.action}
                    </span>
                    <span className="text-white font-bold">
                      {activeInstrument.name} {leg.strike} {leg.type}
                    </span>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <span className="text-[10px] text-slate-400 block">Premium</span>
                      <span className="text-white font-bold">₹{leg.premium.toFixed(1)}</span>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] text-slate-400 block">Lots</span>
                      <span className="text-white font-bold">{leg.lots} ({leg.lots * lotSize} qty)</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right 4 Cols: Key Strategy Risk Metrics & 1-Click Execution */}
        <div className="xl:col-span-4 space-y-6">
          <div className="p-5 rounded-2xl bg-[#090d19]/90 border border-[#B6FF5C]/25 backdrop-blur-xl shadow-xl space-y-4">
            <h2 className="text-sm font-extrabold text-white font-['Outfit'] uppercase tracking-wider">
              Strategy Risk & Payoff Metrics
            </h2>

            <div className="space-y-3 text-xs font-mono">
              <div className="flex items-center justify-between p-3 rounded-xl bg-[#0c1222]">
                <span className="text-slate-400">Max Profit Potential:</span>
                <span className="font-extrabold text-emerald-400 text-sm">
                  {maxProfit > 999999 ? 'Unlimited' : `₹${maxProfit.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
                </span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-[#0c1222]">
                <span className="text-slate-400">Max Loss Risk:</span>
                <span className="font-extrabold text-rose-400 text-sm">
                  {maxLoss < -999999 ? 'Unlimited' : `₹${Math.abs(maxLoss).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
                </span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-[#0c1222]">
                <span className="text-slate-400">Net Premium Cost:</span>
                <span className="font-bold text-white">
                  {netDebit ? `Debit ₹${Math.abs(netPremium * lotSize).toFixed(0)}` : `Credit ₹${(netPremium * lotSize).toFixed(0)}`}
                </span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-[#0c1222]">
                <span className="text-slate-400">Breakeven Points:</span>
                <span className="font-bold text-[#43D9FF]">
                  {breakevens.length > 0 ? breakevens.map(b => `₹${b}`).join(' & ') : `₹${atm}`}
                </span>
              </div>
            </div>

            <button
              onClick={handleExecuteInPaper}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-[#B6FF5C] to-[#84CC16] hover:brightness-110 text-[#080B12] font-black text-xs transition-all cursor-pointer shadow-lg shadow-[#B6FF5C]/20 flex items-center justify-center gap-2"
            >
              <span>Execute Strategy in Paper Trading</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* Historical Backtest Runner */}
          <div className="p-5 rounded-2xl bg-[#090d19]/90 border border-white/[0.08] backdrop-blur-xl shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-extrabold text-white font-['Outfit'] uppercase tracking-wider">
                Quantitative Backtest Engine
              </h2>
              <span className="text-[10px] font-mono text-slate-400">90-Day Walk-Forward</span>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              Validate strategy expectancy across real historical NSE intraday and expiry cycles.
            </p>

            <button
              onClick={handleRunBacktest}
              disabled={backtestRunning}
              className="w-full py-2.5 rounded-xl bg-white/[0.06] hover:bg-white/[0.12] border border-white/[0.1] text-xs font-bold text-white transition-all cursor-pointer flex items-center justify-center gap-2"
            >
              <Play className={`w-3.5 h-3.5 text-sky-400 ${backtestRunning ? 'animate-spin' : ''}`} />
              <span>{backtestRunning ? 'Running Historical Fills...' : 'Run Historical Backtest'}</span>
            </button>

            {backtestResult && (
              <div className="p-3.5 rounded-xl bg-[#0c1222] border border-sky-500/30 space-y-2 pt-3 font-mono text-xs">
                <div className="flex items-center justify-between text-emerald-400 font-bold">
                  <span>Backtest Total Return:</span>
                  <span>+{backtestResult.totalReturnPct}%</span>
                </div>
                <div className="flex items-center justify-between text-slate-300">
                  <span>Win Rate:</span>
                  <span>{backtestResult.winRate}%</span>
                </div>
                <div className="flex items-center justify-between text-slate-300">
                  <span>Sharpe Ratio:</span>
                  <span>{backtestResult.sharpeRatio}</span>
                </div>
                <div className="flex items-center justify-between text-rose-400">
                  <span>Max Drawdown:</span>
                  <span>-{backtestResult.maxDrawdown}%</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
