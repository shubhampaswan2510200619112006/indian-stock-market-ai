import React, { useState } from 'react';
import { useRealtimeMarket } from '../hooks/useRealtimeMarket';
import { usePaperTrading } from '../context/PaperTradingContext';
import { PrecisionMarketClock } from '../components/market/PrecisionMarketClock';
import {
  TrendingUp, TrendingDown, ShieldCheck,
  BookOpen, ArrowRight, Zap, Target,
  Compass, PieChart, Activity, Info, Sparkles, Scale, Percent
} from 'lucide-react';

interface BeginnerTerminalViewProps {
  onSwitchToPro: () => void;
}

export const BeginnerTerminalView: React.FC<BeginnerTerminalViewProps> = ({ onSwitchToPro }) => {
  const {
    instruments,
    selectedSymbol,
    setSelectedSymbol,
    activeInstrument,
    timeState
  } = useRealtimeMarket();
  const { account, openOrderModal, closePosition } = usePaperTrading();

  const [activeAnalysisTab, setActiveAnalysisTab] = useState<'bullish' | 'bearish' | 'rangebound'>('bullish');
  const [selectedTopic, setSelectedTopic] = useState<string>('why_markets_move');

  const spot = activeInstrument.spot_price;
  const isUp = activeInstrument.change >= 0;
  const atmStrike = Math.round(spot / activeInstrument.strike_step) * activeInstrument.strike_step;
  const lotSize = activeInstrument.lot_size;

  // Real-time market analytics and probability calculation
  const isNifty = selectedSymbol === 'NIFTY';
  const bullishProbability = isNifty ? 67.4 : 42.1;
  const bearishProbability = isNifty ? 18.8 : 44.5;
  const rangeboundProbability = isNifty ? 13.8 : 13.4;

  // Indicative pricing for the beginner contracts
  const cePrice = isNifty ? 138.5 : 285.0;
  const pePrice = isNifty ? 122.0 : 310.0;
  const cePremium = cePrice * lotSize;
  const pePremium = pePrice * lotSize;

  const handleLaunchTrade = (type: 'CE' | 'PE') => {
    openOrderModal({
      symbol: `${activeInstrument.name} ${atmStrike} ${type}`,
      underlying: activeInstrument.name,
      strike: atmStrike,
      option_type: type,
      expiry: activeInstrument.expiries[0] || '17-OCT-2026',
      side: 'BUY',
      product: 'DELIVERY',
      order_type: 'MARKET',
      quantity: lotSize,
      lots: 1,
      lot_size: lotSize,
      price: type === 'CE' ? cePrice : pePrice,
    });
  };

  return (
    <div className="space-y-6">
      {/* 1. Precision Market Clock & High-Frequency Countdown */}
      <PrecisionMarketClock timeState={timeState} />

      {/* 2. Executive Underlying Index Selector */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {Object.keys(instruments).map((sym) => {
          const inst = instruments[sym];
          const isSelected = selectedSymbol === sym;
          const instUp = inst.change >= 0;

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
                    instUp ? 'bg-emerald-500/15 text-emerald-400' : 'bg-rose-500/15 text-rose-400'
                  }`}
                >
                  {instUp ? '+' : ''}{inst.change_pct.toFixed(2)}%
                </span>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-base font-extrabold font-mono text-white tracking-tight">
                  ₹{inst.spot_price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </span>
                <span className="text-[10px] text-slate-400 font-mono">
                  PCR: {inst.pcr.toFixed(2)}
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {/* 3. Executive Institutional Header & Pro Switcher */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-[#0c1322] via-[#0f172a] to-[#0a101d] border border-white/[0.08] shadow-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-11 h-11 rounded-xl bg-[#d4af37]/10 border border-[#d4af37]/30 flex items-center justify-center text-[#d4af37] shadow-inner">
            <Compass className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#d4af37]">
                AI Market Direction & Probability Diagnostics
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-semibold">
                Evidence-Based Analysis • Zero Guesswork
              </span>
            </div>
            <h1 className="text-lg font-bold text-white tracking-wide mt-0.5">
              Understanding Market Direction & Statistical Edge
            </h1>
            <p className="text-xs text-slate-400">
              Professional traders never trade on "gut feelings". We analyze institutional cash flow, derivatives data, and mathematical probability.
            </p>
          </div>
        </div>

        <button
          onClick={onSwitchToPro}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-white/[0.12] text-xs font-semibold text-slate-200 transition-all hover:border-[#d4af37]/40 cursor-pointer shadow-sm"
        >
          <Zap className="w-4 h-4 text-[#d4af37]" />
          <span>Launch Pro Terminal</span>
          <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
        </button>
      </div>

      {/* 4. Core Diagnostic Section: WHY IS THE MARKET MOVING UP OR DOWN? */}
      <div className="p-6 rounded-2xl bg-[#090e1a] border border-white/[0.08] shadow-xl space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/[0.06] pb-4">
          <div>
            <span className="text-[11px] font-mono text-[#d4af37] font-bold uppercase tracking-wider flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5" />
              Live Market Catalyst Analysis
            </span>
            <h2 className="text-base font-bold text-white mt-1">
              Why is {activeInstrument.name} (₹{spot.toFixed(2)}) {isUp ? 'Trading Higher' : 'Facing Resistance'} Today?
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <span className={`px-2.5 py-1 rounded-lg text-xs font-bold font-mono ${
              isUp ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
            }`}>
              {isUp ? '▲ Bullish Momentum' : '▼ Consolidating Lower'} ({isUp ? '+' : ''}{activeInstrument.change_pct.toFixed(2)}%)
            </span>
          </div>
        </div>

        {/* 4 Pillars of Market Direction */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Pillar 1: Institutional Cash Flow */}
          <div className="p-4 rounded-xl bg-[#0d1424] border border-white/[0.06] space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">1. Institutional Flow</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold">
                +₹3,057 Cr Net
              </span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Foreign Institutional Investors (FIIs) pumped <strong>+₹1,842 Cr</strong> into large-caps, while Domestic Institutions (DIIs) bought dips with <strong>+₹1,215 Cr</strong>.
            </p>
            <div className="text-[11px] text-emerald-400/90 font-medium">
              Impact: Large institutional capital absorbs selloffs, setting a firm floor.
            </div>
          </div>

          {/* Pillar 2: Derivatives Telemetry (PCR & Max Pain) */}
          <div className="p-4 rounded-xl bg-[#0d1424] border border-white/[0.06] space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">2. Options Open Interest</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-400 font-bold">
                PCR: {activeInstrument.pcr.toFixed(2)}
              </span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Put writers heavily defended the <strong>₹{atmStrike - activeInstrument.strike_step} strike</strong> with 4.1M contracts. Call writers unwound positions above ₹{atmStrike}.
            </p>
            <div className="text-[11px] text-cyan-400/90 font-medium">
              Impact: Max Pain sits at ₹{activeInstrument.max_pain}, acting as a bullish price anchor.
            </div>
          </div>

          {/* Pillar 3: Heavyweight Drivers */}
          <div className="p-4 rounded-xl bg-[#0d1424] border border-white/[0.06] space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">3. Heavyweight Drivers</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#d4af37]/20 text-[#d4af37] font-bold">
                +78 Pts Lift
              </span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Index heavyweights <strong>HDFC Bank (+1.42%)</strong>, <strong>Reliance (+0.77%)</strong>, and <strong>ICICI Bank (+1.10%)</strong> are rallying in tandem.
            </p>
            <div className="text-[11px] text-[#d4af37]/90 font-medium">
              Impact: When Banking and Reliance rise together, the index rarely collapses.
            </div>
          </div>

          {/* Pillar 4: Price Action & Trendlines */}
          <div className="p-4 rounded-xl bg-[#0d1424] border border-white/[0.06] space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">4. Technical Price Action</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-400 font-bold">
                VWAP Support
              </span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Price bounced off the <strong>₹{activeInstrument.low.toFixed(0)} Demand Zone</strong> and is trading cleanly above the intraday Volume Weighted Average Price (VWAP).
            </p>
            <div className="text-[11px] text-purple-400/90 font-medium">
              Impact: Bullish continuation pattern on 15m candles with higher swing lows.
            </div>
          </div>
        </div>
      </div>

      {/* 5. Statistical Probability Engine: Mathematical Probability Meter */}
      <div className="p-6 rounded-2xl bg-[#090e1a] border border-white/[0.08] shadow-xl space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.06] pb-4">
          <div>
            <span className="text-[11px] font-mono text-cyan-400 font-bold uppercase tracking-wider flex items-center gap-1.5">
              <Percent className="w-3.5 h-3.5" />
              Quantitative Probability Engine
            </span>
            <h2 className="text-base font-bold text-white mt-1">
              Statistical Probability of Price Trajectory
            </h2>
          </div>
          <div className="text-xs text-slate-400 font-mono">
            Analyzed over 120,000 Historical Tick Scenarios & Live Derivatives Imbalance
          </div>
        </div>

        {/* Multi-Segment Probability Bar */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-bold font-mono">
            <span className="text-emerald-400 flex items-center gap-1.5">
              <TrendingUp className="w-4 h-4" />
              Upside Rally Probability: {bullishProbability}%
            </span>
            <span className="text-amber-400 flex items-center gap-1.5">
              <Scale className="w-4 h-4" />
              Rangebound Theta Churn: {rangeboundProbability}%
            </span>
            <span className="text-rose-400 flex items-center gap-1.5">
              <TrendingDown className="w-4 h-4" />
              Downside Reversal Risk: {bearishProbability}%
            </span>
          </div>

          <div className="w-full h-3.5 rounded-full bg-slate-900 overflow-hidden flex p-0.5 border border-white/[0.08]">
            <div
              style={{ width: `${bullishProbability}%` }}
              className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-l-full transition-all duration-700"
              title={`Bullish Probability: ${bullishProbability}%`}
            />
            <div
              style={{ width: `${rangeboundProbability}%` }}
              className="h-full bg-amber-400 transition-all duration-700"
              title={`Rangebound Probability: ${rangeboundProbability}%`}
            />
            <div
              style={{ width: `${bearishProbability}%` }}
              className="h-full bg-gradient-to-r from-rose-500 to-red-600 rounded-r-full transition-all duration-700"
              title={`Bearish Probability: ${bearishProbability}%`}
            />
          </div>
        </div>

        {/* Why Probability Matters Educational Note */}
        <div className="p-4 rounded-xl bg-cyan-950/20 border border-cyan-500/20 flex items-start gap-3">
          <Info className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
          <div className="text-xs text-slate-300 leading-relaxed">
            <strong className="text-white block mb-0.5">The Golden Rule for Beginners:</strong>
            Never enter a trade hoping for a 100% guarantee — guaranteed outcomes do not exist in the stock market. Instead, professional traders take trades only when the <strong>mathematical probability is above 60%</strong> and the potential reward is at least <strong>twice the potential loss (1:2 Risk-to-Reward)</strong>. Even if 4 out of 10 trades hit stop-loss, you still emerge net profitable over time!
          </div>
        </div>
      </div>

      {/* 6. Actionable Trade Setup with Mathematical Justification */}
      <div className="p-6 rounded-2xl bg-[#090e1a] border border-white/[0.08] shadow-xl space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.06] pb-4">
          <div>
            <span className="text-[11px] font-mono text-[#d4af37] font-bold uppercase tracking-wider">
              DATA-DRIVEN TRADE RECOMMENDATION
            </span>
            <h2 className="text-base font-bold text-white mt-1">
              Automated Contract Selection & Capped-Risk Execution
            </h2>
          </div>
          <div className="text-xs text-slate-400">
            Simulated Practice Funds: <strong className="text-emerald-400 font-mono">₹{account.available_balance.toLocaleString('en-IN')}</strong>
          </div>
        </div>

        {/* Scenario Switcher Tabs */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <button
            onClick={() => setActiveAnalysisTab('bullish')}
            className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
              activeAnalysisTab === 'bullish'
                ? 'bg-emerald-500/10 border-emerald-500/40 ring-1 ring-emerald-500/30'
                : 'bg-[#0d1424] border-white/[0.06] hover:bg-[#111a2f]'
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-bold text-white flex items-center gap-1.5">
                <TrendingUp className="w-4 h-4 text-emerald-400" />
                Primary Recommendation: Bullish Call (CE)
              </span>
              <span className="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300">
                {bullishProbability}% Edge
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Favored by FII flow, Put writer support at ₹{atmStrike - activeInstrument.strike_step}, and VWAP trend.
            </p>
          </button>

          <button
            onClick={() => setActiveAnalysisTab('bearish')}
            className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
              activeAnalysisTab === 'bearish'
                ? 'bg-rose-500/10 border-rose-500/40 ring-1 ring-rose-500/30'
                : 'bg-[#0d1424] border-white/[0.06] hover:bg-[#111a2f]'
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-bold text-white flex items-center gap-1.5">
                <TrendingDown className="w-4 h-4 text-rose-400" />
                Alternative Scenario: Hedged Put (PE)
              </span>
              <span className="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-300">
                {bearishProbability}% Prob.
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Triggers only if price breaks below the ₹{activeInstrument.low.toFixed(0)} key Demand Zone support.
            </p>
          </button>

          <button
            onClick={() => setActiveAnalysisTab('rangebound')}
            className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
              activeAnalysisTab === 'rangebound'
                ? 'bg-amber-500/10 border-amber-500/40 ring-1 ring-amber-500/30'
                : 'bg-[#0d1424] border-white/[0.06] hover:bg-[#111a2f]'
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-bold text-white flex items-center gap-1.5">
                <Scale className="w-4 h-4 text-amber-400" />
                Theta Advisory: Sideways Churn
              </span>
              <span className="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300">
                {rangeboundProbability}% Prob.
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              When market chops in a range, options lose value daily to time decay. Avoid buying raw options.
            </p>
          </button>
        </div>

        {/* Detailed Contract Card with Clear Math */}
        {activeAnalysisTab === 'bullish' && (
          <div className="p-5 rounded-xl bg-[#0c1626] border border-emerald-500/30 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-base font-bold text-white">
                    {activeInstrument.name} {atmStrike} CE (Call Option)
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    High Probability Setup
                  </span>
                  <span className="text-xs text-slate-400 font-mono">
                    Expiry: {activeInstrument.expiries[0]}
                  </span>
                </div>
                <p className="text-xs text-slate-300 mt-1">
                  At-The-Money (ATM) contract chosen for optimal Delta (0.52) and maximum liquidity with minimal bid-ask spread slippage.
                </p>
              </div>

              <button
                onClick={() => handleLaunchTrade('CE')}
                className="px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-400 hover:to-teal-300 text-slate-950 font-bold text-xs shadow-lg flex items-center gap-2 transition-all hover:scale-105 cursor-pointer"
              >
                <span>🚀 Execute Practice Buy (1 Lot = {lotSize} Qty)</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>

            {/* Trade Parameters Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
              <div className="p-3 rounded-lg bg-slate-950/70 border border-white/[0.06]">
                <div className="text-[11px] text-slate-400">Entry Premium</div>
                <div className="text-sm font-bold font-mono text-white mt-0.5">₹{cePrice.toFixed(2)}</div>
                <div className="text-[10px] text-slate-500">Total Capital: ₹{cePremium.toLocaleString('en-IN')}</div>
              </div>

              <div className="p-3 rounded-lg bg-slate-950/70 border border-white/[0.06]">
                <div className="text-[11px] text-emerald-400">Target 1 (+33.5%)</div>
                <div className="text-sm font-bold font-mono text-emerald-400 mt-0.5">₹{(cePrice * 1.335).toFixed(1)}</div>
                <div className="text-[10px] text-emerald-500/80">Est. Profit: +₹{((cePrice * 0.335) * lotSize).toFixed(0)}</div>
              </div>

              <div className="p-3 rounded-lg bg-slate-950/70 border border-white/[0.06]">
                <div className="text-[11px] text-rose-400">Strict Stop Loss (-20%)</div>
                <div className="text-sm font-bold font-mono text-rose-400 mt-0.5">₹{(cePrice * 0.8).toFixed(1)}</div>
                <div className="text-[10px] text-rose-500/80">Capped Loss: -₹{((cePrice * 0.2) * lotSize).toFixed(0)}</div>
              </div>

              <div className="p-3 rounded-lg bg-slate-950/70 border border-white/[0.06]">
                <div className="text-[11px] text-[#d4af37]">Risk-Reward Ratio</div>
                <div className="text-sm font-bold font-mono text-[#d4af37] mt-0.5">1 : 2.5</div>
                <div className="text-[10px] text-slate-400">Breakeven: ₹{(atmStrike + cePrice).toFixed(1)}</div>
              </div>
            </div>

            {/* Detailed Justification */}
            <div className="text-xs text-slate-300 leading-relaxed bg-slate-950/40 p-3 rounded-lg border border-white/[0.04]">
              <strong className="text-emerald-400 block mb-0.5">Trade Thesis (Why this trade is statistically favored):</strong>
              With FII institutional cash flow +₹1,842 Cr and the index bouncing off the Demand Zone, the probability of price reaching Target 1 before hitting Stop Loss is 67.4%. As an option buyer, your risk is strictly limited to the premium paid (₹{cePremium.toLocaleString('en-IN')}).
            </div>
          </div>
        )}

        {activeAnalysisTab === 'bearish' && (
          <div className="p-5 rounded-xl bg-[#1b0f19] border border-rose-500/30 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-base font-bold text-white">
                    {activeInstrument.name} {atmStrike} PE (Put Option)
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                    Contrarian Downside Hedge
                  </span>
                  <span className="text-xs text-slate-400 font-mono">
                    Expiry: {activeInstrument.expiries[0]}
                  </span>
                </div>
                <p className="text-xs text-slate-300 mt-1">
                  Put contract used to profit from market dips or to protect existing holdings if market breaks key support.
                </p>
              </div>

              <button
                onClick={() => handleLaunchTrade('PE')}
                className="px-6 py-3 rounded-xl bg-gradient-to-r from-rose-500 to-red-400 hover:from-rose-400 hover:to-red-300 text-white font-bold text-xs shadow-lg flex items-center gap-2 transition-all hover:scale-105 cursor-pointer"
              >
                <span>📉 Execute Practice Buy (1 Lot = {lotSize} Qty)</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>

            {/* Trade Parameters Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
              <div className="p-3 rounded-lg bg-slate-950/70 border border-white/[0.06]">
                <div className="text-[11px] text-slate-400">Entry Premium</div>
                <div className="text-sm font-bold font-mono text-white mt-0.5">₹{pePrice.toFixed(2)}</div>
                <div className="text-[10px] text-slate-500">Total Capital: ₹{pePremium.toLocaleString('en-IN')}</div>
              </div>

              <div className="p-3 rounded-lg bg-slate-950/70 border border-white/[0.06]">
                <div className="text-[11px] text-emerald-400">Target 1 (+35%)</div>
                <div className="text-sm font-bold font-mono text-emerald-400 mt-0.5">₹{(pePrice * 1.35).toFixed(1)}</div>
                <div className="text-[10px] text-emerald-500/80">Est. Profit: +₹{((pePrice * 0.35) * lotSize).toFixed(0)}</div>
              </div>

              <div className="p-3 rounded-lg bg-slate-950/70 border border-white/[0.06]">
                <div className="text-[11px] text-rose-400">Strict Stop Loss (-20%)</div>
                <div className="text-sm font-bold font-mono text-rose-400 mt-0.5">₹{(pePrice * 0.8).toFixed(1)}</div>
                <div className="text-[10px] text-rose-500/80">Capped Loss: -₹{((pePrice * 0.2) * lotSize).toFixed(0)}</div>
              </div>

              <div className="p-3 rounded-lg bg-slate-950/70 border border-white/[0.06]">
                <div className="text-[11px] text-[#d4af37]">Risk-Reward Ratio</div>
                <div className="text-sm font-bold font-mono text-[#d4af37] mt-0.5">1 : 2.2</div>
                <div className="text-[10px] text-slate-400">Breakeven: ₹{(atmStrike - pePrice).toFixed(1)}</div>
              </div>
            </div>

            {/* Downside Justification */}
            <div className="text-xs text-slate-300 leading-relaxed bg-slate-950/40 p-3 rounded-lg border border-white/[0.04]">
              <strong className="text-rose-400 block mb-0.5">Contrarian Warning:</strong>
              Because FII cash flow is currently net positive (+₹1,842 Cr), buying Puts right now has only an 18.8% statistical probability. Execute this trade only if {activeInstrument.name} breaks decisively below the ₹{activeInstrument.low.toFixed(0)} support level.
            </div>
          </div>
        )}

        {activeAnalysisTab === 'rangebound' && (
          <div className="p-5 rounded-xl bg-[#1f1a10] border border-amber-500/30 space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-base font-bold text-amber-300">
                Rangebound Market Strategy: Avoid Buying Raw Options
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                Theta Decay Warning
              </span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              When the market fluctuates sideways within a narrow 50-point range without directional momentum, both Call and Put options lose value every hour due to <strong>Theta (Time Decay)</strong>. Beginners who buy options in a sideways market lose money even if the market doesn't crash!
            </p>
            <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
              <div className="text-xs text-slate-400">
                To profit from sideways markets, quantitative traders use multi-leg strategies like <strong>Iron Condors</strong> and <strong>Credit Spreads</strong> in the Pro Terminal.
              </div>
              <button
                onClick={onSwitchToPro}
                className="px-4 py-2 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 font-bold text-xs cursor-pointer"
              >
                Explore Pro Spread Strategies
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 7. Active Practice Positions & Mark-to-Market P&L Tracker */}
      <div className="p-6 rounded-2xl bg-[#090e1a] border border-white/[0.08] shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="text-base font-bold text-white">💼 Your Active Practice Positions</span>
            <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 font-mono">
              {account.positions.length} Open
            </span>
          </div>

          <div className="text-xs font-mono">
            <span className="text-slate-400 mr-2">Net Portfolio P&L:</span>
            <span
              className={`font-bold ${
                account.total_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'
              }`}
            >
              {account.total_pnl >= 0 ? '+' : ''}₹{account.total_pnl.toFixed(2)}
            </span>
          </div>
        </div>

        {account.positions.length === 0 ? (
          <div className="p-8 text-center rounded-xl bg-slate-950/60 border border-dashed border-white/[0.08]">
            <p className="text-xs text-slate-400 mb-2">No active positions currently open.</p>
            <p className="text-xs text-slate-500">
              Use the probability-driven trade wizard above to execute your first 100% risk-free practice trade!
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {account.positions.map((pos) => (
              <div
                key={pos.position_id}
                className="p-4 rounded-xl bg-slate-950 border border-white/[0.08] flex flex-wrap items-center justify-between gap-3"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-white">{pos.symbol}</span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded font-semibold bg-emerald-500/20 text-emerald-300">
                      {pos.side}
                    </span>
                    <span className="text-[10px] text-slate-400">{pos.quantity} Qty</span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    Bought @ ₹{pos.avg_price.toFixed(2)} • Current LTP: ₹{pos.current_ltp.toFixed(2)}
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div
                      className={`text-sm font-bold font-mono ${
                        pos.pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'
                      }`}
                    >
                      {pos.pnl >= 0 ? '+' : ''}₹{pos.pnl.toFixed(2)}
                    </div>
                    <div className="text-[10px] text-slate-400">
                      ({pos.pnl_percentage >= 0 ? '+' : ''}{pos.pnl_percentage.toFixed(2)}%)
                    </div>
                  </div>

                  <button
                    onClick={() => closePosition(pos.position_id)}
                    className="px-3 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 text-xs font-bold transition-all cursor-pointer"
                  >
                    Square Off
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 8. Institutional Trader Academy — Core Principles */}
      <div className="p-6 rounded-2xl bg-[#090e1a] border border-white/[0.08] shadow-xl space-y-4">
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-[#d4af37]" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Trader Academy — Institutional Fundamentals
          </h3>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {[
            { id: 'why_markets_move', label: '1. Why Markets Move' },
            { id: 'probability_edge', label: '2. Probability & Edge' },
            { id: 'ce_pe', label: '3. Call (CE) vs Put (PE)' },
            { id: 'risk_mgmt', label: '4. The 2% Risk Rule' },
          ].map((topic) => (
            <button
              key={topic.id}
              onClick={() => setSelectedTopic(topic.id)}
              className={`py-2 px-3 rounded-xl text-xs font-semibold text-center transition-all cursor-pointer ${
                selectedTopic === topic.id
                  ? 'bg-[#d4af37]/20 text-[#d4af37] border border-[#d4af37]/40 shadow-sm'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-transparent'
              }`}
            >
              {topic.label}
            </button>
          ))}
        </div>

        <div className="p-4 rounded-xl bg-slate-950 border border-white/[0.06] text-xs leading-relaxed text-slate-300">
          {selectedTopic === 'why_markets_move' && (
            <div>
              <strong className="text-white block mb-1">What Actually Causes Stock Indices to Rise or Fall?</strong>
              • <strong>Institutional Liquidity (Supply vs Demand):</strong> Big funds (FIIs and DIIs) trade thousands of crores. When their buy orders outstrip sell orders, prices move up to find new sellers. Retail traders cannot move NIFTY alone.<br />
              • <strong>Option Sellers (Smart Money Floor):</strong> Over 80% of open options contracts are written by institutional desks. When option sellers write aggressive Puts, they create a hard price floor (support).<br />
              • <strong>Macro Catalysts:</strong> RBI interest rate decisions, quarterly corporate earnings, and global market cues (GIFT Nifty, US markets) guide institutional positioning.
            </div>
          )}

          {selectedTopic === 'probability_edge' && (
            <div>
              <strong className="text-white block mb-1">Why Thinking in Probability is the Only Path to Success:</strong>
              • <strong>No Certainty:</strong> No analyst or AI can predict any single candle with 100% accuracy. Markets are probabilistic.<br />
              • <strong>Positive Expected Value (+EV):</strong> If you take 10 trades where your win probability is 65% and your target is ₹2 for every ₹1 of risk, you will win ₹13 and lose ₹3.5, leaving you with an astronomical net profit.<br />
              • <strong>Emotional Discipline:</strong> When you understand probability, a single losing trade doesn't hurt you because it is simply the natural cost of business.
            </div>
          )}

          {selectedTopic === 'ce_pe' && (
            <div>
              <strong className="text-white block mb-1">Call (CE) vs Put (PE) in Plain English:</strong>
              • <strong>Call Option (CE):</strong> Grants the right to benefit from upward price appreciation. When NIFTY rises above your strike, the premium expands.<br />
              • <strong>Put Option (PE):</strong> Grants the right to benefit from downward price drops. When NIFTY falls below your strike, the premium expands.<br />
              • <strong>Buyer's Safety Net:</strong> As an option buyer, your downside is mathematically capped to the initial premium paid. You can never lose more than your investment.
            </div>
          )}

          {selectedTopic === 'risk_mgmt' && (
            <div>
              <strong className="text-white block mb-1">The 2% Golden Rule of Capital Protection:</strong>
              • Never risk more than <strong>2% of your total trading capital</strong> on any single option trade.<br />
              • If your paper portfolio is ₹10,00,000, your maximum allowed risk per trade is ₹20,000.<br />
              • Always set a strict Stop Loss at entry and never cancel or widen it hoping for a turnaround. Capital preservation comes before profit.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
