import React, { useState } from 'react';
import {
  Layers, Activity, Info, Sparkles, Filter,
  TrendingUp, TrendingDown, BookOpen, HelpCircle,
  BarChart2, ShieldCheck, Zap
} from 'lucide-react';
import { OptionChainTableDesk } from '../components/options/OptionChainTableDesk';
import { PCRMaxPainCard } from '../components/options/PCRMaxPainCard';
import { GreeksMatrix } from '../components/options/GreeksMatrix';
import { OptionChainTable } from '../components/options/OptionChainTable';
import { useRealtimeMarket } from '../hooks/useRealtimeMarket';
import { OptionChainSnapshot } from '../types/market';

interface OptionsChainPageViewProps {
  chain?: OptionChainSnapshot;
  expiries?: string[];
}

export const OptionsChainPageView: React.FC<OptionsChainPageViewProps> = ({
  chain: initialChain,
  expiries: initialExpiries = [],
}) => {
  const {
    instruments,
    selectedSymbol,
    setSelectedSymbol,
    selectedExpiry,
    setSelectedExpiry,
    activeInstrument,
    chainRows,
  } = useRealtimeMarket();

  const [viewMode, setViewMode] = useState<'standard' | 'greeks' | 'beginner'>('standard');
  const [strikeFilterRange, setStrikeFilterRange] = useState<'all' | 'atm5' | 'atm10'>('atm10');

  // Filter rows around ATM if selected
  const atm = Math.round(activeInstrument.spot_price / activeInstrument.strike_step) * activeInstrument.strike_step;
  const filteredRows = chainRows.filter((r) => {
    if (strikeFilterRange === 'all') return true;
    const diff = Math.abs(r.strike - atm) / activeInstrument.strike_step;
    if (strikeFilterRange === 'atm5') return diff <= 5;
    if (strikeFilterRange === 'atm10') return diff <= 10;
    return true;
  });

  const pcr = activeInstrument.pcr;
  const pcrStatus = pcr >= 1.2 ? 'Bullish Sentiment' : pcr <= 0.8 ? 'Bearish Sentiment' : 'Neutral Equilibrium';

  return (
    <div className="space-y-6">
      {/* ── 1. Top Options Control & Mode Header ── */}
      <div className="p-4 rounded-2xl bg-[#080d19]/95 border border-[#B6FF5C]/25 backdrop-blur-xl shadow-xl">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <h1 className="text-lg font-black text-white font-['Outfit'] tracking-tight">
                NSE Derivatives Option Chain & Strike Matrix
              </h1>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[#B6FF5C]/15 text-[#B6FF5C] border border-[#B6FF5C]/30">
                LIVE PAPER EXECUTION
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Real-time open interest, implied volatility, Greeks & instant buy/sell order desk
            </p>
          </div>

          {/* View Mode Switcher */}
          <div className="flex items-center bg-[#060a14] p-1 rounded-xl border border-white/[0.08] gap-1 text-xs font-['Outfit']">
            <button
              onClick={() => setViewMode('standard')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all cursor-pointer font-bold ${
                viewMode === 'standard'
                  ? 'bg-[#B6FF5C]/20 text-[#B6FF5C] border border-[#B6FF5C]/40 shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Layers className="w-3.5 h-3.5 text-emerald-400" />
              <span>Interactive Strike Matrix</span>
            </button>

            <button
              onClick={() => setViewMode('greeks')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all cursor-pointer font-bold ${
                viewMode === 'greeks'
                  ? 'bg-[#43D9FF]/20 text-[#43D9FF] border border-[#43D9FF]/40 shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Activity className="w-3.5 h-3.5 text-[#43D9FF]" />
              <span>Black-76 Greeks Desk</span>
            </button>

            <button
              onClick={() => setViewMode('beginner')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all cursor-pointer font-bold ${
                viewMode === 'beginner'
                  ? 'bg-[#B6FF5C]/20 text-[#B6FF5C] border border-[#B6FF5C]/40 shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <HelpCircle className="w-3.5 h-3.5 text-sky-400" />
              <span>Beginner Explainer</span>
            </button>
          </div>
        </div>

        {/* ── Summary Analytics Bar (PCR, Max Pain, ATM Straddle Cost) ── */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-3 border-t border-white/[0.06] text-xs font-mono">
          <div className="p-2.5 rounded-xl bg-[#0c1222] border border-white/[0.04]">
            <span className="text-[10px] text-slate-400 uppercase">Underlying Spot</span>
            <div className="text-sm font-extrabold text-white mt-0.5">
              ₹{activeInstrument.spot_price.toLocaleString('en-IN', { minimumFractionDigits: 1 })}
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-[#0c1222] border border-white/[0.04]">
            <span className="text-[10px] text-slate-400 uppercase">Put-Call Ratio (PCR)</span>
            <div className="text-sm font-extrabold text-emerald-400 mt-0.5 flex items-center justify-between">
              <span>{pcr.toFixed(2)}</span>
              <span className="text-[10px] text-slate-400 font-sans">{pcrStatus}</span>
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-[#0c1222] border border-white/[0.04]">
            <span className="text-[10px] text-slate-400 uppercase">Max Pain Strike</span>
            <div className="text-sm font-extrabold text-[#f6d776] mt-0.5">
              ₹{activeInstrument.max_pain}
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-[#0c1222] border border-white/[0.04]">
            <span className="text-[10px] text-slate-400 uppercase">Strike Filter Range</span>
            <div className="flex items-center gap-1 mt-1">
              {(['atm5', 'atm10', 'all'] as const).map((rng) => (
                <button
                  key={rng}
                  onClick={() => setStrikeFilterRange(rng)}
                  className={`px-1.5 py-0.5 rounded text-[10px] uppercase font-bold transition-all cursor-pointer ${
                    strikeFilterRange === rng
                      ? 'bg-[#B6FF5C]/25 text-[#B6FF5C] border border-[#B6FF5C]/50'
                      : 'bg-white/[0.06] text-slate-400 hover:text-white'
                  }`}
                >
                  {rng === 'atm5' ? '±5 ATM' : rng === 'atm10' ? '±10 ATM' : 'All'}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── 2. Primary Views ── */}
      {viewMode === 'standard' && (
        <OptionChainTableDesk
          instrument={activeInstrument}
          instruments={instruments}
          selectedSymbol={selectedSymbol}
          onSelectSymbol={setSelectedSymbol}
          selectedExpiry={selectedExpiry}
          onSelectExpiry={setSelectedExpiry}
          rows={filteredRows}
        />
      )}

      {viewMode === 'greeks' && (
        <div className="space-y-6">
          <GreeksMatrix />
          <OptionChainTable
            chain={initialChain || {
              underlying: selectedSymbol,
              spot_price: activeInstrument.spot_price,
              expiry: selectedExpiry,
              atm_strike: atm,
              pcr: activeInstrument.pcr,
              total_call_oi: 1250000,
              total_put_oi: 1180000,
              max_pain: activeInstrument.max_pain,
              iv_regime: 'NORMAL',
              rows: [],
              status: 'HISTORICAL',
            }}
            atmStrike={atm}
          />
        </div>
      )}

      {viewMode === 'beginner' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 rounded-2xl bg-[#090d19]/90 border border-white/[0.08] backdrop-blur-xl">
          <div className="space-y-4">
            <h2 className="text-base font-extrabold text-white font-['Outfit'] flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-[#43D9FF]" />
              How Options Work — Plain Language Guide
            </h2>

            <div className="p-4 rounded-xl bg-[#0c1222] border border-white/[0.06] space-y-2 text-xs text-slate-300 leading-relaxed">
              <strong className="text-emerald-400 block font-['Outfit'] text-sm">
                📈 Call Options (CE) — When you expect the market to RISE
              </strong>
              <p>
                Buying a Call gives you the right to profit if {activeInstrument.name} moves above the strike price before expiry ({selectedExpiry}). Your risk is limited to the premium paid, while upside is uncapped.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-[#0c1222] border border-white/[0.06] space-y-2 text-xs text-slate-300 leading-relaxed">
              <strong className="text-rose-400 block font-['Outfit'] text-sm">
                📉 Put Options (PE) — When you expect the market to FALL
              </strong>
              <p>
                Buying a Put allows you to profit if {activeInstrument.name} drops below the strike price. It acts like an insurance policy against falling market prices.
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <h2 className="text-base font-extrabold text-white font-['Outfit'] flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-emerald-400" />
              Current Sentiment & High Probability Strike
            </h2>

            <div className="p-4 rounded-xl bg-[#0c1222] border border-white/[0.06] space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">At-The-Money (ATM) Strike:</span>
                <span className="font-bold text-white font-mono text-sm">₹{atm}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Put-Call Ratio Sentiment:</span>
                <span className="font-bold text-emerald-400 font-mono">{pcrStatus} ({pcr.toFixed(2)})</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Institutional Max Pain Pin:</span>
                <span className="font-bold text-[#43D9FF] font-mono">₹{activeInstrument.max_pain}</span>
              </div>

              <button
                onClick={() => setViewMode('standard')}
                className="w-full mt-2 py-2.5 rounded-xl bg-gradient-to-r from-[#B6FF5C] to-[#84CC16] text-[#080B12] font-black text-xs transition-all cursor-pointer shadow-lg shadow-[#B6FF5C]/20"
              >
                Go to Live Order Pad Desk →
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
